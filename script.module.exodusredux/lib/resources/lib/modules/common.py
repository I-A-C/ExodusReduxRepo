# -*- coding: UTF-8 -*-

import HTMLParser
import json
import random
import re
import urllib2
import urlparse
import requests,os,time
import xbmc,xbmcaddon

USERDATA_PATH = xbmc.translatePath('special://home/userdata/addon_data')
ADDON_DATA = os.path.join(USERDATA_PATH,'script.module.exodusredux')
full_file = os.path.join(ADDON_DATA,'Log.txt')

def clean_title(title):
    if title == None: return
    title = str(title)
    title = re.sub('&#(\d);', '', title)
    title = re.sub('(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', title)
    title = title.replace('&quot;', '\"').replace('&amp;', '&')
    title = re.sub('\n|([[].+?[]])|([(].+?[)])|\s(vs|v[.])\s|(:|;|-|"|,|\'|\_|\.|\?)|\s', '', title)
    return title.lower()

def clean_search(title):
    if title == None: return
    title = title.lower()
    title = re.sub('&#(\d+);', '', title)
    title = re.sub('(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', title)
    title = title.replace('&quot;', '\"').replace('&amp;', '&')
    title = re.sub('\\\|/|\(|\)|\[|\]|\{|\}|-|:|;|\*|\?|"|\'|<|>|\_|\.|\?', ' ', title).lower()
    title = ' '.join(title.split())
    return title


def send_log(name,Time,count,title,year,season = '', episode = ''):
    if not os.path.exists(full_file):
        full_write = open(full_file,"w")
    elif os.path.exists(full_file):
        full_write = open(full_file,'a')
    if count ==0:
        count = 'Check Scraper/NoLinks'
    if episode != '':
        title = title + '('+year+') : S'+season+' E'+episode
    else:
        title = title + '('+year+')'
    Print = '<######################################################\n#        Universalscraper: %s' %(str(name))+'\n#        Tested with: '+str(title)+'\n#        Links returned: %s' %(str(count))+'\n#        Time to Complete: %s' %(str(round(Time,2)))+'\n#######################################################>' 
    full_write.write(Print+'\n')
'''
    print '<######################################################'
    print '#        Tested with: %s' %(str(title))
    print '#        Universalscraper: %s' %(str(name))
    print '#        Links returned: %s' %(str(count))
    print '#        Time to Complete: %s' %(str(round(Time,2)))
    print '#######################################################>'  
    return
''' 
def Del_LOG():
  ADDON_DATA = os.path.join(USERDATA_PATH,'script.module.exodusredux')
  full_file = ADDON_DATA + '/Log.txt'
  if os.path.exists(full_file):
    os.remove(full_file)
    

def error_log(name,Txt):
    if not os.path.exists(full_file):
        full_write = open(full_file,"w")
    elif os.path.exists(full_file):
        full_write = open(full_file,'a')
    if 'list index out of range' in Txt:
        Txt	= Txt + '\n (Probably doesn\'t have movie or search needs editing)'
    Print = ':>>>>        Scraper: %s' %(str(name))+'\n:>>>>        LogNotice: %s' %(str(Txt))
    full_write.write(Print+'\n')
'''
    print ':>>>>        Scraper: %s' %(str(name))
    print ':>>>>        LogNotice: %s' %(str(Txt))
    return 
'''

def random_agent():
    BR_VERS = [
        ['%s.0' % i for i in xrange(18, 43)],
        ['37.0.2062.103', '37.0.2062.120', '37.0.2062.124', '38.0.2125.101', '38.0.2125.104', '38.0.2125.111',
         '39.0.2171.71', '39.0.2171.95', '39.0.2171.99', '40.0.2214.93', '40.0.2214.111',
         '40.0.2214.115', '42.0.2311.90', '42.0.2311.135', '42.0.2311.152', '43.0.2357.81', '43.0.2357.124',
         '44.0.2403.155', '44.0.2403.157', '45.0.2454.101', '45.0.2454.85', '46.0.2490.71',
         '46.0.2490.80', '46.0.2490.86', '47.0.2526.73', '47.0.2526.80'],
        ['11.0']]
    WIN_VERS = ['Windows NT 10.0', 'Windows NT 7.0', 'Windows NT 6.3', 'Windows NT 6.2', 'Windows NT 6.1',
                'Windows NT 6.0', 'Windows NT 5.1', 'Windows NT 5.0']
    FEATURES = ['; WOW64', '; Win64; IA64', '; Win64; x64', '']
    RAND_UAS = ['Mozilla/5.0 ({win_ver}{feature}; rv:{br_ver}) Gecko/20100101 Firefox/{br_ver}',
                'Mozilla/5.0 ({win_ver}{feature}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{br_ver} Safari/537.36',
                'Mozilla/5.0 ({win_ver}{feature}; Trident/7.0; rv:{br_ver}) like Gecko']
    index = random.randrange(len(RAND_UAS))
    return RAND_UAS[index].format(win_ver=random.choice(WIN_VERS), feature=random.choice(FEATURES),
                                  br_ver=random.choice(BR_VERS[index]))


def replaceHTMLCodes(txt):
    txt = re.sub("(&#[0-9]+)([^;^0-9]+)", "\\1;\\2", txt)
    txt = HTMLParser.HTMLParser().unescape(txt)
    txt = txt.replace("&quot;", "\"")
    txt = txt.replace("&amp;", "&")
    return txt


def vk(url):
    try:
        try:
            oid, id = urlparse.parse_qs(urlparse.urlparse(url).query)['oid'][0], \
                      urlparse.parse_qs(urlparse.urlparse(url).query)['id'][0]
        except:
            oid, id = re.compile('\/video(.*)_(.*)').findall(url)[0]
        try:
            hash = urlparse.parse_qs(urlparse.urlparse(url).query)['hash'][0]
        except:
            hash = vk_hash(oid, id)

        u = 'http://api.vk.com/method/video.getEmbed?oid=%s&video_id=%s&embed_hash=%s' % (oid, id, hash)

        headers = {'User-Agent': random_agent()}

        request = urllib2.Request(u, headers=headers)
        result = urllib2.urlopen(request).read()

        result = re.sub(r'[^\x00-\x7F]+', ' ', result)

        try:
            result = json.loads(result)['response']
        except:
            result = vk_private(oid, id)

        url = []
        try:
            url += [{'quality': '720', 'url': result['url720']}]
        except:
            pass
        try:
            url += [{'quality': '540', 'url': result['url540']}]
        except:
            pass
        try:
            url += [{'quality': '480', 'url': result['url480']}]
        except:
            pass
        if not url == []: return url
        try:
            url += [{'quality': '360', 'url': result['url360']}]
        except:
            pass
        if not url == []: return url
        try:
            url += [{'quality': '240', 'url': result['url240']}]
        except:
            pass

        if not url == []: return url

    except:
        return


def vk_hash(oid, id):
    try:
        url = 'http://vk.com/al_video.php?act=show_inline&al=1&video=%s_%s' % (oid, id)

        headers = {'User-Agent': random_agent()}

        request = urllib2.Request(url, headers=headers)
        result = urllib2.urlopen(request).read()
        result = result.replace('\'', '"').replace(' ', '')

        hash = re.compile('"hash2":"(.+?)"').findall(result)
        hash += re.compile('"hash":"(.+?)"').findall(result)
        hash = hash[0]

        return hash
    except:
        return


def vk_private(oid, id):
    try:
        url = 'http://vk.com/al_video.php?act=show_inline&al=1&video=%s_%s' % (oid, id)

        headers = {'User-Agent': random_agent()}

        request = urllib2.Request(url, headers=headers)
        result = urllib2.urlopen(request).read()
        result = re.compile('var vars *= *({.+?});').findall(result)[0]
        result = re.sub(r'[^\x00-\x7F]+', ' ', result)
        result = json.loads(result)

        return result
    except:
        return


def odnoklassniki(url):
    try:
        url = re.compile('//.+?/.+?/([\w]+)').findall(url)[0]
        url = 'http://ok.ru/dk?cmd=videoPlayerMetadata&mid=%s' % url

        headers = {'User-Agent': random_agent()}

        request = urllib2.Request(url, headers=headers)
        result = urllib2.urlopen(request).read()
        result = re.sub(r'[^\x00-\x7F]+', ' ', result)

        result = json.loads(result)['videos']

        try:
            hd = [{'quality': '1080', 'url': i['url']} for i in result if i['name'] == 'full']
        except:
            pass
        try:
            hd += [{'quality': 'HD', 'url': i['url']} for i in result if i['name'] == 'hd']
        except:
            pass
        try:
            sd = [{'quality': 'SD', 'url': i['url']} for i in result if i['name'] == 'sd']
        except:
            pass
        try:
            sd += [{'quality': 'SD', 'url': i['url']} for i in result if i['name'] == 'low']
        except:
            pass
        try:
            sd += [{'quality': 'SD', 'url': i['url']} for i in result if i['name'] == 'lowest']
        except:
            pass
        try:
            sd += [{'quality': 'SD', 'url': i['url']} for i in result if i['name'] == 'mobile']
        except:
            pass

        url = hd + sd[:1]
        if not url == []: return url

    except:
        return

def googletag(url):
    quality = re.compile('itag=(\d*)').findall(url)
    quality += re.compile('=m(\d*)$').findall(url)
    try:
        quality = quality[0]
    except:
        return []

    if quality in ['37', '137', '299', '96', '248', '303', '46']:
        return [{'quality': '1080', 'url': url}]
    elif quality in ['22', '84', '136', '298', '120', '95', '247', '302', '45', '102']:
        return [{'quality': '720', 'url': url}]
    elif quality in ['35', '44', '135', '244', '94']:
        return [{'quality': '480', 'url': url}]
    elif quality in ['18', '34', '43', '82', '100', '101', '134', '243', '93']:
        return [{'quality': '480', 'url': url}]
    elif quality in ['5', '6', '36', '83', '133', '242', '92', '132']:
        return [{'quality': '480', 'url': url}]
    else:
        return []

def filter_host(host):
    if host not in ['example.com', 'allvid.ch', 'anime-portal.org', 'anyfiles.pl',
                    'www.apnasave.club', 'castamp.com', 'clicknupload.com', 'clicknupload.me',
                    'clicknupload.link', 'cloud.mail.ru', 'cloudy.ec', 'cloudy.eu', 'cloudy.sx',
                    'cloudy.ch', 'cloudy.com', 'daclips.in', 'daclips.com', 'dailymotion.com',
                    'ecostream.tv', 'exashare.com', 'uame8aij4f.com', 'yahmaib3ai.com',
                    'facebook.com', 'filepup.net', 'fileweed.net', 'flashx.tv', 'googlevideo.com',
                    'googleusercontent.com', 'get.google.com', 'plus.google.com', 'googledrive.com',
                    'drive.google.com', 'docs.google.com', 'gorillavid.in', 'gorillavid.com',
                    'grifthost.com', 'hugefiles.net', 'indavideo.hu', 'kingfiles.net', 'mail.ru',
                    'my.mail.ru', 'm.my.mail.ru', 'videoapi.my.mail.ru', 'api.video.mail.ru',
                    'mersalaayitten.com', 'mersalaayitten.co', 'mersalaayitten.us', 'movdivx.com',
                    'divxme.com', 'movpod.net', 'movpod.in', 'movshare.net', 'wholecloud.net',
                    'vidgg.to', 'mp4stream.com', 'myvi.ru', 'nosvideo.com', 'noslocker.com',
                    'novamov.com', 'auroravid.to', 'ok.ru', 'odnoklassniki.ru', 'openload.io',
                    'openload.co', 'oload.tv', 'playwire.com', 'promptfile.com', 'rapidvideo.com',
                    'raptu.com', 'rutube.ru', 'videos.sapo.pt', 'speedvideo.net', 'streamcloud.eu',
                    'streamin.to', 'stream.moe', 'streamplay.to', 'teramixer.com', 'thevid.net',
                    'thevideo.me', 'toltsd-fel.tk', 'toltsd-fel.xyz', 'trollvid.net', 'trollvid.io',
                    'mp4edge.com', 'tudou.com', 'tune.pk', 'upload.af', 'uploadx.org', 'uploadz.co',
                    'uptobox.com', 'uptostream.com', 'veoh.com', 'videa.hu', 'videoget.me',
                    'videohut.to', 'videoraj.ec', 'videoraj.eu', 'videoraj.sx', 'videoraj.ch',
                    'videoraj.com', 'videoraj.to', 'videoraj.co', 'bitvid.sx', 'videoweed.es',
                    'videoweed.com', 'videowood.tv', 'byzoo.org', 'playpanda.net', 'videozoo.me',
                    'videowing.me', 'easyvideo.me', 'play44.net', 'playbb.me', 'video44.net',
                    'vidlox.tv', 'vidmad.net', 'tamildrive.com', 'vid.me', 'vidup.me', 'vimeo.com',
                    'vivo.sx', 'vk.com', 'vshare.eu', 'watchers.to', 'watchonline.to',
                    'everplay.watchpass.net', 'weshare.me', 'xvidstage.com', 'yourupload.com',
                    'yucache.net', 'youtube.com', 'youtu.be', 'youtube-nocookie.com',
                    'youwatch.org', 'chouhaa.info', 'aliez.me', 'ani-stream.com', 'bestream.tv',
                    'blazefile.co', 'divxstage.eu', 'divxstage.net', 'divxstage.to', 'cloudtime.to',
                    'downace.com', 'entervideo.net', 'estream.to', 'fastplay.sx', 'fastplay.cc',
                    'goodvideohost.com', 'jetload.tv', 'letwatch.us', 'letwatch.to', 'vidshare.us',
                    'megamp4.net', 'mp4engine.com', 'mp4upload.com', 'myvidstream.net',
                    'nowvideo.eu', 'nowvideo.ch', 'nowvideo.sx', 'nowvideo.co', 'nowvideo.li',
                    'nowvideo.fo', 'nowvideo.at', 'nowvideo.ec', 'playedto.me', 'www.playhd.video',
                    'www.playhd.fo', 'putload.tv', 'shitmovie.com', 'rapidvideo.ws',
                    'speedplay.xyz', 'speedplay.us', 'speedplay1.site', 'speedplay.pw',
                    'speedplay1.pw', 'speedplay3.pw', 'speedplayy.site', 'speedvid.net',
                    'spruto.tv', 'stagevu.com', 'streame.net', 'thevideos.tv', 'tusfiles.net',
                    'userscloud.com', 'usersfiles.com', 'vidabc.com', 'vidcrazy.net',
                    'uploadcrazy.net', 'thevideobee.to', 'videocloud.co', 'vidfile.net',
                    'vidhos.com', 'vidto.me', 'vidtodo.com', 'vidup.org', 'vidzi.tv', 'vodlock.co',
                    'vshare.io', 'watchvideo.us', 'watchvideo2.us', 'watchvideo3.us',
                    'watchvideo4.us', 'watchvideo5.us', 'watchvideo6.us', 'watchvideo7.us',
                    'watchvideo8.us', 'watchvideo9.us', 'watchvideo10.us', 'watchvideo11.us',
                    'watchvideo12.us', 'zstream.to']:
        return False
    return True

def check_playable(url):
    """
checks if passed url is a live link
    :param str url: stream url
    :return: playable stream url or None
    :rtype: str or None
    """
    import urllib
    import requests
    try:
        headers = url.rsplit('|', 1)[1]
    except:
        headers = ''
    headers = urllib.quote_plus(headers).replace('%3D', '=') if ' ' in headers else headers
    headers = dict(urlparse.parse_qsl(headers))

    result = None
    try:
        if url.startswith('http') and '.m3u8' in url:
            result = requests.head(url.split('|')[0], headers=headers, timeout=5)
            if result is None:
                return None

        elif url.startswith('http'):
            result = requests.head(url.split('|')[0], headers=headers, timeout=5)
            if result is None:
                return None
    except:
        pass

    return result


def get_rd_domains():
    import xbmc
    import xbmcaddon
    import os
    try:
        from sqlite3 import dbapi2 as database
    except:
        from pysqlite2 import dbapi2 as database
    import datetime

    cache_location = os.path.join(
            xbmc.translatePath(xbmcaddon.Addon("script.module.exodusredux").getAddonInfo('profile')).decode('utf-8'),
            'url_cache.db')
    try:
            dbcon = database.connect(cache_location)
            dbcur = dbcon.cursor()
            try:
                dbcur.execute("SELECT * FROM version")
                match = dbcur.fetchone()
            except:
                dbcur.execute("CREATE TABLE version (""version TEXT)")
                dbcur.execute("INSERT INTO version Values ('0.5.4')")
                dbcon.commit()
            dbcur.execute(
                "CREATE TABLE IF NOT EXISTS rd_domains (""domains TEXT, ""added TEXT"");")
    except Exception as e:
        pass

    try:
        sources = []
        dbcur.execute(
            "SELECT * FROM rd_domains")
        match = dbcur.fetchone()
        t1 = int(re.sub('[^0-9]', '', str(match[1])))
        t2 = int(datetime.datetime.now().strftime("%Y%m%d%H%M"))
        update = abs(t2 - t1) > 60 * 24
        if update is False:
            sources = json.loads(match[0])
            return sources
    except Exception as e:
        pass
    url = 'https://api.real-debrid.com/rest/1.0/hosts/domains'
    domains = requests.get(url).json()
    try:
        dbcur.execute("DELETE FROM rd_domains WHERE added = %s" %(match[1]))
    except:
        pass
    dbcur.execute("INSERT INTO rd_domains Values (?, ?)", (
                        json.dumps(domains),
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    dbcon.commit()
    return domains
