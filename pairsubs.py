import xmlrpc.client
import base64
import zlib
import srt
from bs4 import UnicodeDammit
import textwrap
import itertools
from datetime import timedelta

COLUMN_WIDTH = 40

class Opensubtitles:
    ''' opensuntitles.org access'''

    user_agent = "TemporaryUserAgen"

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

    def _save_sub_(self, name, data):
        with open(name, 'w') as f:
            f.write(data)

    def _save_sub_bin_(self, name, data):
        with open(name, 'wb') as f:
            f.write(data)

    def search_sub(self, imdbid, lang):
        '''
        Search the subtitles in Opensubtitles database
        by IMBD id and a language.
        Return dict as described in
        http://trac.opensubtitles.org/projects/opensubtitles/wiki/XMLRPC#SearchSubtitles
        Args:
            imdbid (int): Movie's IMDB id
            lang (str): Language of subtitles in ISO639 format
        Returns:
            sub (dict): subtitle in Opensubtitles API format
        '''
        try:
            result = self.proxy.SearchSubtitles(self.token,
                         [{'imdbid': str(imdbid), 'sublanguageid': lang}], [100])
        except xmlrpc.client.ProtocolError as err:
            print("Opensubtitles API protocol error: {0}".format(err))
        else:

            return self._select_sub_(result['data'])

    def download_sub(self, sub, save=True, save_orig=True, encoding=None):
        '''
        Download subtitles from subtitles.org.
        Return subtitles file as a bytearray
        '''
        try:
            result = self.proxy.DownloadSubtitles(self.token, [sub['IDSubtitleFile']])
        except xmlrpc.client.ProtocolError as err:
            print("Opensubtitles API protocol error: {0}".format(err))
        else:
            data_zipped = base64.b64decode(result['data'][0]['data'])
            data_bytes = zlib.decompress(data_zipped, 15+32)
            return data_bytes

class Subs:

    def __init__(self, sub_b, encoding=None,
                 lang=None, movie_name=None, imdbid=None):
        self.lang = lang if lang else ""
        self.movie_name = movie_name if movie_name else ""
        self.imdbid = imdbid if imdbid else ""
        self.encoding = encoding
        self.sub_b = sub_b

        # Decode bytearray to Unicode string
        if self.encoding:
            data = sub_b.decode(self.encoding)
        else:
            data = UnicodeDammit(sub_b).unicode_markup

        self.sub = list(srt.parse(data))
        self._fix_subtitles_()

    def save(self, name=None):
        if name:
            file_name = name
        else:
            file_name = '_'.join([self.movie_name, self.imdbid, self.lang])
            file_name = file_name.replace(' ', '_')
            file_name = file_name.replace('"', '')
            file_name += '.srt'

        if self.encoding:
            data = self.sub_b.decode(self.encoding)
            with open(file_name, 'w') as f:
                f.write(data)
        else:
            with open(file_name, 'wb') as f:
                f.write(self.sub_b)

    @classmethod
    def read(cls, name, encoding=None,
            lang=None, movie_name=None, imdbid=None):

        subs_args = {'encoding':encoding, 'lang':lang,
                      'movie_name':movie_name, 'imdbid':imdbid}
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
            start (float): 0-100 - start time of subtitles (percent of total length)
            length (int):  duration in seconds
        '''
        lines =[]
        start_td = self.sub[-1].end * start/100
        end_td = start_td + timedelta(seconds=length)
        for line in self.sub:
            if line.start >= start_td and line.end <= end_td:
                lines.append(line.content)
            if line.start > end_td:
                return lines
        return lines

class SubPair:
    ''' Pair of subtitles'''

    def __init__(self, subs):
        '''
        Args:
            subs: list of <Subs> objects
        '''
        self.subs = subs


    @classmethod
    def download(cls, imdbid, lang1, lang2, enc1=None, enc2=None):
        osub = Opensubtitles()
        osub.login()

        subs = []
        sub_args = {'lang1':lang1, 'lang2':lang2}
        i = 1
        for lang, enc in [(lang1, enc1), (lang2, enc2)]:
            sub = osub.search_sub(imdbid, lang)
            if sub:
                sub_args['movie_name'] = sub['MovieName']
                sub_args['imdbid'] = sub['IDMovieImdb']

                print("Downloading {} ...".format(lang))
                sub_bytes = osub.download_sub(sub)
                subs_args['sub_bin'+str(i)] = sub_bytes
                i += 1
                # Decode bytearray to Unicode string
                if enc:
                    data = sub_bytes.decode(enc)
                else:
                    data = UnicodeDammit(sub_bytes).unicode_markup

                subs.append(SubPair._to_subtitles_(data))
            else:
                print("Subtitles #{} isn't found".format(imdbid))
                osub.logout()
                return None

        osub.logout()
        return cls(*subs, **subs_args)

    @classmethod
    def _to_subtitles_(cls, data_in):
        return list(srt.parse(data_in))

    def _get_sub_info(self, sub):
        length = sub[-1].start
        return length

    def _analyze_pair_(self, sub1, sub2):
        self.max_time = min(self._get_sub_info(sub1),
                            self._get_sub_info(sub2))

    def _equalize_subs_(self):
        if self.sub1[-1].start > self.sub2[-1].start:
            coeff = self.sub2[-1].start/self.sub1[-1].start
            max_sub = self.sub1
        else:
            coeff = self.sub1[-1].start/self.sub2[-1].start
            max_sub = self.sub2

        for s in max_sub:
            s.start *= coeff

    def decode_sub(self, select, encoding):
        if select == 1:
            self.sub1 = SubPair._to_subtitles_(self.sub_bin1.decode(encoding))
        elif select == 2:
            self.sub2 = SubPair._to_subtitles_(self.sub_bin2.decode(encoding))
        else:
            print("Error: select must be 1 or to")

    def save(self, save_orig=False):
        for sub in [(self.sub1,self.lang1), (self.sub2, self.lang2)]:

            file_name = '_'.join([self.movie_name, self.imdbid, self.lang])
            file_name = file_name.replace(' ', '_')
            file_name = file_name.replace('"', '')
            file_name += '.srt'
            with open(file_name, 'w') as f:
                f.write(_sub_to_str_(sub))
        if save_orig:
            for sub in [self.sub_bin1, self.sub_bin2]:
                file_name = '_'.join([sub['MovieName'], sub['IDMovieImdb'], sub['ISO639']])
                file_name = file_name.replace(' ', '_')
                file_name = file_name.replace('"', '')
                file_name += '_orig'
                file_name += '.srt'
                with open(file_name, 'w') as f:
                    f.write(sub)

    def _sub_to_str_(self, sub):
        # convert list of Subtitles to string
        sub_str = ""
        i = 1
        for s in sub:
            sub_str += str(i)
            sub_str += "{} --> {}".format(sub.start, sub.end)
            sub_str += sub.content
            sub_str += "\n"



    def print_pair(self, offset=0, count=1):

        data = []
        for s in self.subs:
            #import ipdb; ipdb.set_trace()
            lines = s.get_lines(offset, count)
            line = '\n'.join(lines)
            line_l = line.splitlines()
            res = []
            for l in line.splitlines():
                res += textwrap.wrap(l,COLUMN_WIDTH)

            data.append(res)

        out = itertools.zip_longest(*data,  fillvalue="")

        for s in out:
            print("{}  |  {}".format(s[0]+(COLUMN_WIDTH-len(s[0]))*" ", s[1]))

    def _get_lines_(self, sub, start_time, count, shift=0):
        start_index = 0
        for s in sub:
            if s.start >= start_time:
                start_index = sub.index(s)
                break
        return sub[start_index+shift:start_index+shift+count]

    def _wrap_line_(self, subtitles):
        res = []
        for s in subtitles:
            res += textwrap.wrap(s,COLUMN_WIDTH)


if __name__ == '__main__':

    import sys
    offset = int(sys.argv[1])
    count = int(sys.argv[2])

    sub_e = Subs.read("avengers_orig_en.srt")
    sub_r = Subs.read("avengers_orig_ru.srt")

    pp = SubPair([sub_r, sub_e])
    pp.print_pair(offset, count)



    #sub_id = int(sys.argv[1])

    #p = SubPair.download(sub_id, 'ita', 'eng', encoding='cp1251')
    #p = SubPair.download(sub_id, 'rus', 'eng')
    # p = SubPair.read('Deadpool_1431045_ru', 'Deadpool_1431045_en', lang1='rus', lang2='eng')
    # if p:
    #     p.print_pair(20, 20, 6)
    # import ipdb; ipdb.set_trace()
    # p.save()



#     pp = Opensubtitles()
#     pp.login()

#     sub = pp.search_sub(sub_id, 'eng')
#     if sub:
#         print("Downloading En...")
#         s_en = pp.download_sub(sub)
#     else:
#         print("Subtitles #{} isn't found".format(sub_id))
#     sub = pp.search_sub(sub_id, 'rus')
#     if sub:
#         print("Downloading Ru...")
#         s_ru = pp.download_sub(sub)
#     else:
#         print("Subtitles #{} isn't found".format(sub_id))

    # if s_ru and s_en:
    #     d = SubPair(s_ru, s_en)
    #     d.print_pair(35, 20, 0)
    #     import ipdb; ipdb.set_trace()

    #     p = SubPair.load("Luke_Cage_Step_in_the_Arena_4179636_ru","Luke_Cage_Step_in_the_Arena_4179636_en")

    #     p.print_pair(35, 20, 0)
    #     #import ipdb; ipdb.set_trace()


