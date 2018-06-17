import pytest
from pairsubs import *

mocksubs = [
{'SubDownloadsCnt':10, 'MovieReleaseName':'Release_10', 'IDMovieImdb':'ID_10', 'SubLanguageID':'Lang_10'},
{'SubDownloadsCnt':20, 'MovieReleaseName':'Release_20', 'IDMovieImdb':'ID_20', 'SubLanguageID':'Lang_20'},
]

mocksrt = [
"""
1
00:00:01,000 --> 00:00:10,000
Sentence #1

2
00:00:11,000 --> 00:00:20,000
Sentence #2

3
00:00:21,000 --> 00:00:30,000
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

        imdbid = params[0]['imdbid']
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
    sub = os.search_sub(12, "rus")
    assert sub == mocksubs[1]

def test_download_sub(monkeypatch):
    monkeypatch.setattr(xmlrpc.client, 'ServerProxy', mockproxy)

    os = Opensubtitles()
    os.login()
    sub = os.download_sub({'IDSubtitleFile':12})
    assert sub == mocksrt[0].encode()

