import xmlrpc.client
import base64
import zlib
import srt
from bs4 import UnicodeDammit
import textwrap
import itertools

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
        ''' Download subtitles from subtitles.org.
            Return subtitles file as a list of <Subtitle> objects.
            Save argument controls whether the subtitles will be written to a file.
        '''
        try:
            result = self.proxy.DownloadSubtitles(self.token, [sub['IDSubtitleFile']])
        except xmlrpc.client.ProtocolError as err:
            print("Opensubtitles API protocol error: {0}".format(err))
        else:
            data_zipped = base64.b64decode(result['data'][0]['data'])
            data_str = zlib.decompress(data_zipped, 15+32)
            if encoding:
                data = data_str.decode(encoding)
            else:
                data = UnicodeDammit(data_str).unicode_markup

            if save:
                file_name = '_'.join([sub['MovieName'], sub['IDMovieImdb'], sub['ISO639']])
                file_name = file_name.replace(' ', '_')
                file_name = file_name.replace('"', '')
                self._save_sub_(file_name, data)
            if save_orig:
                file_name = '_'.join([sub['MovieName'], sub['IDMovieImdb'], sub['ISO639']])
                file_name = file_name.replace(' ', '_')
                file_name = file_name.replace('"', '')
                file_name += '_orig'
                self._save_sub_bin_(file_name, data_str)
            return list(srt.parse(data))


class SubPair:
    ''' Pair of subtitles'''

    def __init__(self, sub1, sub2):
        '''
        Args:
            sub1: list of Subtitles for the first set
            sub2: list of Subtitles for the second set
        '''
        self.sub1 = sub1
        self.sub2 = sub2
        self._analyze_pair_(sub1, sub2)
        #self._equalize_subs_()

    @classmethod
    def read(cls, file1, file2):
        subs = []
        for file_name in (file1, file2):
            with open(file_name, 'r') as f:
                subs.append(list(srt.parse(f.read())))

        return cls(*subs)

    @classmethod
    def download(cls, imdbid, lang1, lang2, encoding=None):
        osub = Opensubtitles()
        osub.login()

        subs = []

        for lang in [lang1, lang2]:
            sub = osub.search_sub(imdbid, lang)
            if sub:
                print("Downloading {} ...".format(lang))
                subs.append(osub.download_sub(sub, encoding=encoding))
            else:
                print("Subtitles #{} isn't found".format(imdbid))
                return None

        return cls(*subs)

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




    def print_pair(self, offset=0, count=1, shift=0):
        start = self.max_time*offset/100

        s1 = self._get_lines_(self.sub1, start, count)
        pl = self._wrap_line_(s1)

        s2 = self._get_lines_(self.sub2, start, count, shift=shift)
        pr = self._wrap_line_(s2)

        out = itertools.zip_longest(pl, pr, fillvalue="")

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
        line = ""
        for s in subtitles:
            line += s.content
            line += "\n----\n"

        lines = line.splitlines()
        res = []
        for line in lines:
            res += textwrap.wrap(line,COLUMN_WIDTH)
        return res


if __name__ == '__main__':

    import sys
    sub_id = int(sys.argv[1])

    p = SubPair.download(sub_id, 'ita', 'eng', encoding='cp1251')
    if p:
        p.print_pair(20, 20, 6)



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


