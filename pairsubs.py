import xmlrpc.client
import datetime
import base64
import zlib
import srt
from bs4 import UnicodeDammit

lang = ['ru','en']


def select_sub(subtitles, lang):
    rate = 0;
    top_sub = None
    #import ipdb; ipdb.set_trace()

    for sub in subtitles['data']:
        #print(sub)
        if sub['ISO639'] == lang and int(sub['SubDownloadsCnt']) >= rate:
            rate = int(sub['SubDownloadsCnt'])
            top_sub = sub
    print("Select_sub: Lang - {}, Found - {}".format(lang, True if top_sub else False))
    return top_sub

def download_sub(token, proxy, sub):
    result = proxy.DownloadSubtitles(token,[sub['IDSubtitleFile']])
    data_zipped = base64.b64decode(result['data'][0]['data'])
    data_str = zlib.decompress(data_zipped, 15+32)
    data_dec = UnicodeDammit(data_str)
    return list(srt.parse(data_dec.unicode_markup))


def get_subs(imdbid, lang_first, lang_sec):
    proxy = xmlrpc.client.ServerProxy("https://api.opensubtitles.org/xml-rpc")

    login = proxy.LogIn("","","en","TemporaryUserAgent")
    token = login['token']

    result = proxy.SearchSubtitles(token, [
       {'imdbid':str(imdbid), 'sublanguageid':','.join([lang_first, lang_sec])}
    ],[100])

    # divide by language
    sub_first = select_sub(result, lang_first)
    sub_sec = select_sub(result, lang_sec)

    if not sub_first or not sub_sec:
        return None

    s_f = download_sub(token, proxy, sub_first)
    s_s = download_sub(token, proxy, sub_sec)

    login = proxy.LogOut(token)

    return [s_f, s_s]


if __name__ == '__main__':
    subs = get_subs(3322314, 'en', 'ru')
    for i in range(min(len(subs[0]), len(subs[1]))):
        print(subs[0][i].content[:50],subs[1][i].content[:50])
    #import ipdb; ipdb.set_trace()


