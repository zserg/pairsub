import pytest

import srt
import xmlrpc.client
import zlib
import base64

from pairsubs.pairsubs import Subs, SubPair, Opensubtitles

mocksubs = [
{'SubDownloadsCnt':10, 'MovieReleaseName':'Release_10', 'IDMovieImdb':'ID_10', 'SubLanguageID':'Lang_10'},
{'SubDownloadsCnt':20, 'MovieReleaseName':'Release_20', 'IDMovieImdb':'ID_20', 'SubLanguageID':'Lang_20'},
]

mocksubsinfo = [
        {'MovieName':'Name_10', 'SubEncoding':'utf-8', 'SubFileName':'File_10', 'SubLanguageID': 'Lang_10', 'IDMovieImdb': 'imdb_10', 'IDSubtitleFile': 10},
        {'MovieName':'Name_20', 'SubEncoding':'utf-8', 'SubFileName':'File_20', 'SubLanguageID': 'Lang_20', 'IDMovieImdb': 'imdb_20', 'IDSubtitleFile': 20},
]

mocksrt = [
"""1
00:00:01,000 --> 00:00:10,000
Sentence #1

2
00:00:11,000 --> 00:00:20,000
Sentence #2

3
00:00:21,000 --> 00:00:30,000
Sentence #3

4
00:00:31,500 --> 00:00:35,200
Sentence #3

5
00:00:40,020 --> 00:00:43,999
Sentence #3
"""
,
"""
1
00:00:01,000 --> 00:00:10,000
Sentence #4

2
00:00:11,000 --> 00:00:20,000
Sentence #5

3
00:00:21,000 --> 00:00:30,000
Sentence #6
"""
]

class mockproxy():
    '''
    xmlrpc.client.ServerProxy mock class
    '''
    def __init__(self, path):
        pass

    def LogIn(self, login, password, lang, agent):
        return {'token':"42"}

    def SearchSubtitles(self, token, params, count):
        if not token:
            return None

        imdbid = int(params[0]['imdbid'])
        lang = params[0]['sublanguageid']
        cnt = count[0]
        return {'status':'200 OK',
                'data': mocksubs,
                'seconds': 0.1
                }

    def DownloadSubtitles(self, token, params):
        if not token:
            return None

        subs_data = []
        for sub in mocksrt:
            z = zlib.compress(sub.encode())
            b64 = base64.b64encode(z)
            subs_data.append(b64)

        #data_zipped = base64.b64decode(result['data'][0]['data'])
        return {'data':[{'data':subs_data[0]}]}



def test_login(monkeypatch):
    monkeypatch.setattr(xmlrpc.client, 'ServerProxy', mockproxy)

    os = Opensubtitles()
    os.login()
    assert os.token == '42'

def test_search_sub(monkeypatch):
    monkeypatch.setattr(xmlrpc.client, 'ServerProxy', mockproxy)

    os = Opensubtitles()
    os.login()
    sub = os.search_sub("https://www.imdb.com/title/tt1853728/?ref_=nv_sr_1", "rus")
    assert sub == mocksubs[1]

def test_download_sub(monkeypatch):
    monkeypatch.setattr(xmlrpc.client, 'ServerProxy', mockproxy)

    os = Opensubtitles()
    os.login()
    sub = os.download_sub({'IDSubtitleFile':12})
    assert sub == mocksrt[0].encode()



class TestSubs:

    def test_init(self):
        sub_data = mocksrt[0].encode()
        sub_info = mocksubsinfo[0]
        s = Subs(sub_data, sub_info)
        assert s.sub == list(srt.parse(mocksrt[0]))
        #import ipdb; ipdb.set_trace()
        assert s.sub_info == sub_info

    def test_get_sub(self):
        sub_data = mocksrt[0].encode()
        sub_info = mocksubsinfo[0]
        s = Subs(sub_data, sub_info)
        start = 10.5
        end = 25.0
        assert s.get_subs(start, end) == list(srt.parse(mocksrt[0]))[1:3]

