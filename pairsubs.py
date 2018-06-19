import xmlrpc.client
import base64
import zlib
import srt
from bs4 import UnicodeDammit
import textwrap
import itertools
from datetime import timedelta
import random
import os
import json
import codecs


COLUMN_WIDTH = 40

#: Directory in which to store PaiSubs cache.
APP_DIR = '{}/.pairsubs'.format(os.path.expanduser('~'))

#: File in which to store details aboud downloaded subtitles
CACHE_DB = '{}/cache.json'.format(APP_DIR)

class Opensubtitles:
    '''
    Class for opensuntitles.org access
    '''

    user_agent = "TemporaryUserAgent"

    def __init__(self):
        '''Init xml-rpc proxy'''

        self.proxy = xmlrpc.client.ServerProxy(
                "https://api.opensubtitles.org/xml-rpc")

    def logout(self):
        ''' Logout from api.opensubtitles.org.'''

        try:
            self.proxy.LogOut(self.token)
        except xmlrpc.client.ProtocolError as err:
            print("Opensubtitles API protocol error: {0}".format(err))

    def login(self):
        ''' Login into api.opensubtitles.org.'''

        try:
            login = self.proxy.LogIn("", "", "en", "TemporaryUserAgent")
        except xmlrpc.client.ProtocolError as err:
            print("Opensubtitles API protocol error: {0}".format(err))
        else:
            self.token = login['token']

    def _select_sub_(self, subtitles):
        ''' Select subtitles that have maximal downloads count'''
        rate = 0
        top_sub = None

        for sub in subtitles:
            if int(sub['SubDownloadsCnt']) >= rate:
                rate = int(sub['SubDownloadsCnt'])
                top_sub = sub
        return top_sub

    def search_sub(self, imdbid, lang):
        '''
        Search the subtitles in Opensubtitles database
        by IMBD id and a language.
        Return dict as described in
        http://trac.opensubtitles.org/projects/opensubtitles/wiki/XMLRPC#SearchSubtitles
        Args:
            imdbid (int): Movie's IMDB id
            lang (str): Language of subtitles in ISO639 format (3-letter)
        Returns:
            sub (dict): subtitles info in Opensubtitles API format
        '''
        try:
            result = self.proxy.SearchSubtitles(
                    self.token,
                    [{'imdbid': str(imdbid), 'sublanguageid': lang}],
                    [100])
        except xmlrpc.client.ProtocolError as err:
            print("Opensubtitles API protocol error: {0}".format(err))
        else:

            #import ipdb; ipdb.set_trace()
            return self._select_sub_(result['data'])

    def download_sub(self, sub):
        '''
        Download subtitles from subtitles.org.
        Args:
            sub (dict): subtitles info in Opensubtitles API format
        Return:
            data_bytes (bytes): downloaded subtitles
        '''
        try:
            result = self.proxy.DownloadSubtitles(self.token,
                                                  [sub['IDSubtitleFile']])
        except xmlrpc.client.ProtocolError as err:
            print("Opensubtitles API protocol error: {0}".format(err))
        else:
            data_zipped = base64.b64decode(result['data'][0]['data'])
            data_bytes = zlib.decompress(data_zipped, 15+32)
            #import ipdb; ipdb.set_trace()
            return data_bytes


class Subs:
    '''
    Base class for subtitles
    '''

    def __init__(self, sub_data, sub_info = {
                  'SubLanguageID': None,
                  'SubFileName': None,
                  'SubEncoding': None,
                  'MovieName': None,
                  'IDMovieImdb': None}):
        self.sub_b = sub_data
        self.sub_info = sub_info
        #import ipdb; ipdb.set_trace()

        # Decode bytearray to Unicode string
        if self.sub_info['SubEncoding']:
            if self.sub_b.startswith(codecs.BOM_UTF8):
                encoding = 'utf-8-sig'
            else:
                encoding = self.sub_info['SubEncoding']
            data = self.sub_b.decode(encoding)
        else:
            data = UnicodeDammit(self.sub_b).unicode_markup

        #import ipdb; ipdb.set_trace()
        self.sub = self._parse_subtitles_(data)
        self._fix_subtitles_()

    def __repr__(self):
        return "Subs: [{}] [{}] [{}]".format(self.sub_info['MovieName'],
                                             self.sub_info['IDMovieImdb'],
                                             self.sub_info['SubLanguageID'])

    def save(self, name=None):
        with open(file_name, 'wb') as f:
            f.write(self.sub_b)

    @classmethod
    def read(cls, name, encoding=None,
             lang=None, movie_name=None, imdbid=None):

        subs_args = {'encoding': encoding, 'lang': lang,
                     'movie_name': movie_name, 'imdbid': imdbid}
        with open(name, 'rb') as f:
            data = f.read()

        return cls(data, **subs_args)

    def _fix_subtitles_(self):
        t = timedelta(seconds=0)
        i = 0
        for s in self.sub:
            if s.start < t:
                self.sub.pop(i)
                # print("removed: {}-{}".format(s.start, s.content))
            else:
                t = s.end
            i += 1

    def get_lines(self, start, length):
        '''
        Return list of <str> from subtitles
        whose timedelta are between start and stop.
        Args:
            start (timedelta): 0-100 - start time of subtitles
            length (int):  duration in seconds
        '''
        lines = []
        end = start + timedelta(seconds=length)
        for line in self.sub:
            if line.start >= start and line.end <= end:
                lines.append(line.content)
            if line.start > end:
                return lines
        return lines

    def set_encoding(self, encoding):
        self.sub_info['SubEncoding'] = encoding
        data = self.sub_b.decode(self.sub_info['SubEncoding'])
        self.sub = self._parse_subtitles_(data)
        self._fix_subtitles_()

    def _parse_subtitles_(self, data):
        try:
            sub = list(srt.parse(data))
            return sub
        except ValueError as e:
            print("Subtitles parsing failed: {}".format(e))
            return []

class SubPair:
    ''' Pair of subtitles'''

    def __init__(self, subs):
        '''
        Args:
            subs: list of <Subs> objects
        '''
        self._cache_init_()
        self.subs = subs
        self.offset = 0 # offset in seconds betwen subtitles in a pair
        self.coeff = 1  # difference in duration between subtitles in a pair
        #import ipdb; ipdb.set_trace()
        self._append_to_cache_()

    def __repr__(self):
        return "{}, {}".format(self.subs[0].__repr__(),
                               self.subs[1].__repr__())

    @classmethod
    def download(cls, imdbid, lang1, lang2, enc1=None, enc2=None):
        osub = Opensubtitles()
        osub.login()

        subs = []
        for lang, enc in [(lang1, enc1), (lang2, enc2)]:
            sub = osub.search_sub(imdbid, lang)
            if sub:
                print("Downloading {} ...".format(lang))
                sub_b = osub.download_sub(sub)
                s = Subs(sub_b, sub_info = sub)
                subs.append(s)
            else:
                print("Subtitles #{} isn't found".format(imdbid))
                osub.logout()
                return None

        osub.logout()
        return cls(subs)

    def print_pair(self, offset=0, count=1):

        #import ipdb; ipdb.set_trace()
        start_td = self.subs[0].sub[-1].end * offset/100
        data = []
        for s in self.subs:
            lines = s.get_lines(start_td, count)
            line = '\n'.join(lines)
            res = []
            for l in line.splitlines():
                res += textwrap.wrap(l, COLUMN_WIDTH)

            data.append(res)

        out = itertools.zip_longest(*data,  fillvalue="")

        for s in out:
            print("{}  |  {}".format(s[0]+(COLUMN_WIDTH-len(s[0]))*" ", s[1]))

    def print_pair_random(self, count=1):
        offset = random.random() * 100
        self.print_pair(offset, count)

    def save_subs(self):
        for sub in self.subs:
           sub.save()

    def _cache_init_(self):
        '''
        Init cache
        '''
        # verify that the application directory (~/.pairsubs) exists,
        #   else create it
        if not os.path.exists(APP_DIR):
            os.makedirs(APP_DIR)

        # If the cache db doesn't exist we create it.
        # Otherwise we only open for reading
        if not os.path.isfile(CACHE_DB):
            with open(CACHE_DB, 'a'):
                os.utime(CACHE_DB, None)

        self.cache_db = {}

        # We know from above that this file exists so we open it
        #   for reading only.
        with open(CACHE_DB, 'r') as f:
            try:
                self.cache_db = json.load(f)
            except ValueError:
                pass

    def set_params(self, offset, coeff):
        import ipdb; ipdb.set_trace()
        self.offset = offset
        self.coeff = coeff
        if self._is_in_cache_():
            self.cache_db[self._get_key_()]['offset'] = self.offset
            self.cache_db[self._get_key_()]['coeff'] = self.coeff
            self._cache_write_()


    def _get_key_(self):
        return  '_'.join([
                self.subs[0].sub_info['IDSubtitleFile'],
                self.subs[1].sub_info['IDSubtitleFile']
                ])

    def _get_value_(self):
        return  {'offset': self.offset,
                 'coeff': self.coeff,
                 'subs': [
                    self.subs[0].sub_info,
                    self.subs[1].sub_info
                    ]}

    def _cache_write_(self):
        with open(CACHE_DB, 'w') as f:
            f.write(json.dumps(self.cache_db))

    def _append_to_cache_(self):
        # load offset and coeff from cache if exists
        if self._is_in_cache_():
            key = self._get_key_()
            self.offset = self.cache_db[key]['offset']
            self.coeff = self.cache_db[key]['coeff']
        # store info in cache if doesn't exists
        if not self._is_in_cache_():
            key = self._get_key_()
            value = self._get_value_()
            self.cache_db[key] = value
            self._cache_write_()

    def _is_in_cache_(self):
        key = self._get_key_()
        return key in self.cache_db


if __name__ == '__main__':

    import sys
    sub_id = int(sys.argv[1])
    p = SubPair.download(sub_id, 'rus', 'eng')
    p.print_pair(20, 20)
    p.subs[0].set_encoding('cp1251')
    # import ipdb; ipdb.set_trace()
    p.print_pair(20, 20)
    # sub_e = Subs.read("avengers_orig_en.srt")
    # sub_r = Subs.read("avengers_orig_ru.srt")

    # pp = SubPair([sub_r, sub_e])
    # pp.print_pair(offset, count)
