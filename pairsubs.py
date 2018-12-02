import xmlrpc.client
import http.client
import base64
import zlib
import srt
from srt import SRTParseError
from bs4 import UnicodeDammit
from datetime import timedelta
from urllib.parse import urlparse
import random
import os
import json
import codecs
import re
from time import sleep
import pairsubs_gui

import logging
from logging import NullHandler

logger = logging.getLogger(__name__)
logger.addHandler(NullHandler())

COLUMN_WIDTH = 40
OPENSUBTUTLES_MAX_RETRY = 3


#: Directory in which to store PaiSubs cache.
APP_DIR = '{}/.pairsubs'.format(os.path.expanduser('~'))

FILES_DIR = os.path.join(APP_DIR, 'files')

#: File in which to store details aboud downloaded subtitles
CACHE_DB = '{}/cache.json'.format(APP_DIR)

# Opensubtitles API retry count
MAX_RETRY = 5
RETRY_DELAY = 3

# Parse fail
# https://www.imdb.com/title/tt0583453/?ref_=tt_ep_pr


class OpensubtitlesError(Exception):
    def __str__(self):
        return 'Max retry number was exceeded during access to Opensubtitles.org'


class ProxiedTransport(xmlrpc.client.Transport):

    def set_proxy(self, host, port=None, headers=None):
        self.proxy = host, port
        self.proxy_headers = headers

    def make_connection(self, host):
        connection = http.client.HTTPConnection(*self.proxy)
        connection.set_tunnel(host, headers=self.proxy_headers)
        self._connection = host, connection
        return connection


class Opensubtitles:
    """Class for opensuntitles.org access."""
    user_agent = "OS Test User Agent"

    def __init__(self):
        """Init xml-rpc proxy."""
        proxy_url = os.environ.get('http_proxy', '')
        if proxy_url:
            parsed = urlparse(proxy_url).netloc
            transport = ProxiedTransport()
            transport.set_proxy(parsed)
            self.proxy = xmlrpc.client.ServerProxy(
                    "https://api.opensubtitles.org/xml-rpc",
                    transport=transport)
        else:
            self.proxy = xmlrpc.client.ServerProxy(
                    "https://api.opensubtitles.org/xml-rpc")

    def retry(func):
        def wrapper(self, *args, **kwargs):
            for i in range(MAX_RETRY):
                try:
                    res = func(self, *args, **kwargs)
                except (xmlrpc.client.ProtocolError, http.client.ResponseNotReady) as e:
                    logger.info("Retry #{}".format(i+1))
                    sleep(RETRY_DELAY)
                else:
                    return res
            raise OpensubtitlesError
        return wrapper

    @retry
    def logout(self):
        """Logout from api.opensubtitles.org."""
        logger.info("Opensubtitles: Logout...")
        self.proxy.LogOut(self.token)

    @retry
    def login(self):
        """Login into api.opensubtitles.org."""
        logger.info("Opensubtitles: Login...")
        login = self.proxy.LogIn("", "", "en", "TemporaryUserAgent")
        self.token = login['token']

    def _select_sub_(self, subtitles):
        """Select subtitles that have maximal downloads count."""
        rate = 0
        top_sub = None

        for sub in subtitles:
            if int(sub['SubDownloadsCnt']) >= rate:
                rate = int(sub['SubDownloadsCnt'])
                top_sub = sub
        return top_sub

    @retry
    def search_sub(self, imdbid, lang):
        """
        Search the subtitles in Opensubtitles database
        by IMBD id and a language.
        Return dict as described in
        http://trac.opensubtitles.org/projects/opensubtitles/wiki/XMLRPC#SearchSubtitles
        Args:
            `imdbid` (int): Movie's IMDB id
            `lang` (str): Language of subtitles in ISO639 format (3-letter)
        Returns:
            (dict): subtitles info in Opensubtitles API format
        """
        logger.info("Opensubtitles: search...")
        m = re.search(r'\d+', imdbid)
        if m:
            imdb = m[0]
            result = self.proxy.SearchSubtitles(
                    self.token,
                    [{'imdbid': str(imdb), 'sublanguageid': lang}],
                    [100])
            return self._select_sub_(result['data'])

    @retry
    def download_sub(self, sub):
        """
        Download subtitles from subtitles.org.
        Args:
            `sub` (dict): subtitles info in Opensubtitles API format
        Return:
            `data_bytes` (bytes): downloaded subtitles
        """
        logger.info("Opensubtitles: download...")
        result = self.proxy.DownloadSubtitles(self.token,
                                              [sub['IDSubtitleFile']])
        data_zipped = base64.b64decode(result['data'][0]['data'])
        data_bytes = zlib.decompress(data_zipped, 15+32)
        return data_bytes


class Subs:
    """
    Base class for subtitles
    Args:
        `sub_data` (bytes): subtitles in SRT format
        `sub_info` (dict): subtitles information
        `decode` (bool): True if to decode subtitles as SubLanguageID defines
    Attributes:
        `sub_info` (dict): subtitles information
        `sub` (list of `Subtitles`)
    """

    def __init__(self, sub_data, sub_info, decode=True):
        info_keys = ('SubLanguageID',
                     'SubFileName',
                     'SubEncoding',
                     'MovieName',
                     'IDMovieImdb',
                     'IDSubtitleFile')

        self.sub_info = {}
        for k in info_keys:
            self.sub_info[k] = sub_info.get(k, None)

        # Decode bytes to Unicode string
        if decode:
            data_decoded = self.sub_decode(sub_data,
                                           self.sub_info['SubEncoding'])
        else:
            data_decoded = sub_data

        # Parse bytes into a list of Subtitles objects
        self.sub = self._parse_subtitles(data_decoded)

    def __repr__(self):
        return "Subs: [{}] [{}] [{}]".format(self.sub_info['MovieName'],
                                             self.sub_info['IDMovieImdb'],
                                             self.sub_info['SubLanguageID'])

    @staticmethod
    def sub_decode(data, encoding):
        """
        Args:
            `data` (bytes): subtitles in SRT format
            `encoding`: (str): encoding
        """
        if encoding:
            if data.startswith(codecs.BOM_UTF8):
                enc = 'utf-8-sig'
            else:
                enc = encoding
            return data.decode(enc, errors='replace')
        else:
            return UnicodeDammit(data).unicode_markup

    def save(self, name=None):
        """Save subtitles file."""
        data = srt.compose(self.sub)
        file_name = name if name else self.sub_info['SubFileName']
        with open(os.path.join(FILES_DIR, file_name), 'w') as f:
            f.write(data)

    @classmethod
    def read(cls, sub_info):
        """
        Read sibtitles from file.
        Args:
            `sub_info` (dict): subtitles information
        Returns:
            `Subs` object
        """
        name = os.path.join(FILES_DIR, sub_info['SubFileName'])
        with open(name, 'r') as f:
            data = f.read()
        return cls(data, sub_info, decode=False)

    def get_subs(self, start, end):
        """
        Returns list of subtitles whose timedelta is between start and stop.
        Args:
            `start` (float): start time of subtitles (seconds)
            `end` (float): end time of subtitles (seconds)
        Returns:
            list` of `Subtitles`
        """
        subs = []
        for s in self.sub:
            if (s.start >= self.seconds_to_timedelta(start) and
                    s.start <= self.seconds_to_timedelta(end)):
                subs.append(s)
        return subs

    def _parse_subtitles(self, data):
        """
        Parse subtitles from str.
        Args:
            `data` (str): subtitles data
        Returns:
            list of `Subtitles`
        """
        try:
            sub = list(srt.parse(data))
        except (ValueError, SRTParseError) as e:
            logger.error("Subtitles parsing failed: {}".format(e))
            sub = []
        return sub

    def seconds_to_timedelta(self, seconds):
        s = int(seconds)
        ms = seconds - s
        return timedelta(seconds=s,  milliseconds=ms)


class SubPair:
    """Pair of subtitles.
        Attributes:
            `subs`: tuple of two `Subs` objects
            `first_start` (float):
            `first_end` (float):
            `second_start` (float):
            `second_end` (float):
    """
    def __init__(self, subs):
        """
        Args:
            `subs`: tuple of two `Subs` objects
        """
        self.subs = subs
        self.first_start = 0
        self.first_end = subs[0].sub[-1].start.total_seconds()
        self.second_start = 0
        self.second_end = subs[0].sub[-1].start.total_seconds()

    def __repr__(self):
        return "[{}, {}]".format(self.subs[0].__repr__(),
                                 self.subs[1].__repr__())

    @classmethod
    def download(cls, imdbid, lang1, lang2, enc1=None, enc2=None):
        logger.info("Start subtitles download: {} ({}, {})".format(
                                           imdbid, lang1, lang2))
        logger.info("Login into Opensubtitles...")
        osub = Opensubtitles()
        osub.login()

        subs = []
        for lang, enc in [(lang1, enc1), (lang2, enc2)]:
            logger.info("Search {}...".format(lang))
            sub = osub.search_sub(imdbid, lang)
            if sub:
                logger.info("Download {}...".format(lang))
                sub_b = osub.download_sub(sub)
                s = Subs(sub_b, sub)
                if s.sub:
                    subs.append(s)
                else:
                    logger.info("Failed the subtitles parsing".format(lang))
                    return None
            else:
                logger.info("Subtitles #{} aren't found".format(lang))
                osub.logout()
                return None

        osub.logout()
        return cls(subs)

    @classmethod
    def read(cls, info):
        subs = []
        for sub in info['subs']:
            s = Subs.read(sub)
            subs.append(s)
        return cls(subs)

    def get_parallel_subs(self, start, length):
        """
        Args:
            `start` (float): 0-100 percenrage of full length from the begin
            `lenght` (int): duration in seconds
        Returns:
            list of to two lists of `Subtitles`
        """
        first_len = self.first_end - self.first_start
        second_len = self.second_end - self.second_start
        coeff = first_len/second_len
        offset = first_len * start / 100

        f_start = self.first_start + offset
        f_end = f_start + length

        s_start = self.second_start + offset/coeff
        s_end = s_start + length/coeff

        par_subs = []
        for s, params in zip(self.subs, [(f_start, f_end), (s_start, s_end)]):
            subs = s.get_subs(*params)
            par_subs.append(subs)

        return par_subs

    def align_subs(self, left_start, right_start, left_end, right_end):
        self.first_start = self.subs[0].sub[left_start-1].start.total_seconds()
        self.first_end = self.subs[0].sub[left_end-1].start.total_seconds()

        self.second_start = self.subs[1].sub[right_start-1].start.total_seconds()
        self.second_end = self.subs[1].sub[right_end-1].start.total_seconds()

    def save_subs(self):
        for sub in self.subs:
            sub.save()

    def get_id(self):
        return '_'.join([
                self.subs[0].sub_info['IDSubtitleFile'],
                self.subs[1].sub_info['IDSubtitleFile']
                ])

    def get_data(self):
        return {'first_start': self.first_start,
                'first_end': self.first_end,
                'second_start': self.second_start,
                'second_end': self.second_end,
                'subs': [
                    self.subs[0].sub_info,
                    self.subs[1].sub_info
                    ]}


class SubDb():
    """Subtitles Database Class.

    Attributes:
        data: (dict of dicts) SubPairs info dictionary with fields:
            - `sub_id` (str): subpair_info (:obj:`dict`)

            subpair_info (:`obj`:`dict`) : SubPairs info dictionary with fields:
                `first_start`: (float)
                `first_end`: (float)
                `second_start`: (float)
                `second_end`: (float)
                `subs`: sub_info (list of dicts)

                sub_info (dict) : sub info dictionary with fields:
                    `SubLanguageID`: (str)
                    `SubFileName` : (str)
                    `SubEncoding` : (str)
                    `MovieName` :(str)
                    `IDMovieImdb` : (str)
                    `IDSubtitleFile` :(str)

        cache: (dict of {str: `SubPair`}) SubPairs dictionary with fields:
    """
    def __init__(self):
        self.data = self.load_data()
        self.cache = {}

    def load_data(self):
        """Load subtitles info data."""
        # verifies that the application directory (~/.pairsubs) exists,
        #   else create it
        if not os.path.exists(APP_DIR):
            os.makedirs(APP_DIR)

        if not os.path.exists(FILES_DIR):
            os.makedirs(FILES_DIR)

        # If the cache db doesn't exist we create it.
        # Otherwise we only open for reading
        if not os.path.isfile(CACHE_DB):
            with open(CACHE_DB, 'a'):
                os.utime(CACHE_DB, None)

        data = {}

        # We know from above that this file exists so we open it
        #   for reading only.
        with open(CACHE_DB, 'r') as f:
            try:
                data = json.load(f)
            except ValueError:
                pass
        return data

    def is_in_db(self, sub_pair):
        sub_id = sub_pair.get_id()
        return sub_id in self.data

    def add_subpair(self, sub_pair):
        if not self.is_in_db(sub_pair):
            sub_id = sub_pair.get_id()
            sub_data = sub_pair.get_data()
            self.data[sub_id] = sub_data

    def download(self, imdbid, lang1, lang2):
        """
        Downloads subtitles from Opensubtitles.org.
        Args:
            `imdbid` (str): INDB id string (or URL)
            `lang1` (str): first language
            `lang2` (str): second language
        Returns:
            `SubPair` object
        """
        sub_pair = SubPair.download(imdbid, lang1, lang2)
        if sub_pair:
            self.add_subpair(sub_pair)
            self.add_to_cache(sub_pair)
            self.write_db()
            sub_pair.save_subs()
            return sub_pair.get_id()

    def write_db(self):
        # update db data with the alignment data from cache
        keys = ('first_start', 'first_end',
                'second_start', 'second_end')
        for sub_id in self.cache:
            for k in keys:
                self.data[sub_id][k] = getattr(self.cache[sub_id], k)

        with open(CACHE_DB, 'w') as f:
            f.write(json.dumps(self.data))

    def add_to_cache(self, sub_pair):
        sub_id = sub_pair.get_id()
        if sub_id not in self.cache:
            self.cache[sub_id] = sub_pair

    def read_subpair(self, sub_id):
        if sub_id not in self.cache:
            sub_info = self.data[sub_id]
            sub_pair = SubPair.read(sub_info)
            self.add_to_cache(sub_pair)

    def get_subs(self, sub_id=None):
        if self.data:
            if not sub_id:  # get random sub
                sub_id = random.choice(list(self.data.keys()))

            if sub_id not in self.cache:
                self.read_subpair(sub_id)
            position = random.randint(0, 100)
            subs = self.cache[sub_id].get_parallel_subs(position, 20)
            return sub_id, subs

    def get_subs_to_align(self, sub_id, count=4):
        """
        Get subtittles for manual alignment.
        To align you need several subtitles from the begin and the end
        of each subtitle file.
        Args:
            `sub_id` (str): SubPair id
            `count` (int): number of subtitles from the begin and the end
        Returns:
            `subs` (tuple): tuple of 4 lists of `Subtitles`
                    ([`first_begin`], [`second_begin`], [`first_end`], [`second_end`])
        """
        if self.data:
            if sub_id not in self.cache:
                self.read_subpair(sub_id)
            subs = (self.cache[sub_id].subs[0].sub[:count],  # First sub, begin
                    self.cache[sub_id].subs[1].sub[:count],  # Second sub, begin,
                    self.cache[sub_id].subs[0].sub[-1-count:-1],  # First sub, end
                    self.cache[sub_id].subs[1].sub[-1-count:-1],  # Second sub, end
                    )
            return subs

    def delete(self, sub_id):
        """Removes subtitles files."""
        for s in self.data[sub_id]['subs']:
            filename = os.path.join(FILES_DIR, s['SubFileName'])
            try:
                os.remove(filename)
            except FileNotFoundError:
                print('File {} is not found'.format(filename))

        del self.data[sub_id]

        try:
            del self.cache[sub_id]
        except KeyError:
            pass

        self.write_db()

    def align_subs(self, sub_id, left_start, right_start, left_end, right_end):
        if sub_id not in self.cache:
            self.read_subpair(sub_id)
        self.cache[sub_id].align_subs(left_start, right_start, left_end, right_end)
        self.write_db()
        return self.cache[sub_id]


if __name__ == '__main__':
    # import ipdb; ipdb.set_trace()
    logger.setLevel(logging.INFO)

    db = SubDb()
    app = pairsubs_gui.App(db)

    log_box = app.get_search_box()
    loop = app.get_loop()
    log_handler = logging.StreamHandler(pairsubs_gui.SubsLogStream(log_box, loop))
    logger.addHandler(log_handler)

    app.run()
