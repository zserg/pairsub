import xmlrpc.client
import datetime
import base64
import zlib
import srt
from bs4 import UnicodeDammit
from terminaltables import AsciiTable

lang = ['ru','en']

class Opensubtitles:
    ''' opensuntitles.org access'''

    user_agent = "TemporaryUserAgen"

    def __init__(self):
        '''Init xml-rpc proxy'''

        self.proxy = xmlrpc.client.ServerProxy("https://api.opensubtitles.org/xml-rpc")

    def logout(self):
        ''' Logout from api.opensubtitles.org.'''

        try:
            login = self.proxy.LogOut(self.token)
        except xmlrpc.client.ProtocolError as err:
            print("Opensubtitles API protocol error: {0}".format(err))

    def login(self):
        ''' Login into api.opensubtitles.org.'''

        try:
            login = self.proxy.LogIn("","","en","TemporaryUserAgent")
        except xmlrpc.client.ProtocolError as err:
            print("Opensubtitles API protocol error: {0}".format(err))
        else:
            self.token = login['token']

    def _select_sub_(self, subtitles):
        ''' Select subtitles that have maximal downloads count'''
        rate = 0;
        top_sub = None

        for sub in subtitles:
            if int(sub['SubDownloadsCnt']) >= rate:
                rate = int(sub['SubDownloadsCnt'])
                top_sub = sub
        return top_sub

    def _save_sub_(self, name, data):
        with open(name,'w') as f:
            f.write(data)

    def search_sub(self, imdbid, lang):
        '''
        Search the subtitles in Opensubtitles database by IMBD id and a language.
        Return dict as described in http://trac.opensubtitles.org/projects/opensubtitles/wiki/XMLRPC#SearchSubtitles
        Args:
            imdbid (int): Movie's IMDB id
            lang (str): Language of subtitles in ISO639 format
        Returns:
            sub (dict): subtitle in Opensubtitles API format
        '''
        #import ipdb; ipdb.set_trace()
        try:
            result = self.proxy.SearchSubtitles(self.token,
                            [{'imdbid':str(imdbid), 'sublanguageid':lang}],[100])
        except xmlrpc.client.ProtocolError as err:
            print("Opensubtitles API protocol error: {0}".format(err))
        else:

            return self._select_sub_(result['data'])

    def download_sub(self, sub, save = True):
        ''' Download subtitles from subtitles.org.
            Return subtitles file as a list of <Subtitle> objects.
            Save argument controls whether the subtitles will be written to a file.
        '''
        try:
            result = self.proxy.DownloadSubtitles(self.token,[sub['IDSubtitleFile']])
        except xmlrpc.client.ProtocolError as err:
            print("Opensubtitles API protocol error: {0}".format(err))
        else:
            data_zipped = base64.b64decode(result['data'][0]['data'])
            data_str = zlib.decompress(data_zipped, 15+32)
            data = UnicodeDammit(data_str).unicode_markup
            file_name = '_'.join([sub['MovieName'],sub['IDMovieImdb'],sub['ISO639']])
            if save:
                self._save_sub_(file_name, data)
            return list(srt.parse(data))


def print_pair(sub_l, sub_r):
    table_data = []
    for i in range(min(len(sub_l), len(sub_r))):
        row = [sub_l[i].content, sub_r[i].content]
        table_data.append(row)
    table = AsciiTable(table_data)
    print(table.table)


if __name__ == '__main__':
    import sys
    sub_id = int(sys.argv[1])
    pp = Opensubtitles()
    pp.login()
    import ipdb; ipdb.set_trace()

    sub = pp.search_sub(sub_id, 'en')
    if sub:
        s_en = pp.download_sub(sub)
    sub = pp.search_sub(sub_id, 'ru')
    if sub:
        s_ru = pp.download_sub(sub)
    print_pair(s_ru, s_en)


#    import ipdb; ipdb.set_trace()



    #subs = get_subs(3322314, 'en', 'ru')
    #subs = get_subs(2283362, 'en', 'ru')
    # subs = get_subs(3896198, 'en', 'ru')
