# -*- coding: utf-8 -*-

'''
    bennu Add-on

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import os,re,sys,hashlib,urllib,urlparse,json,base64,random,datetime
import xbmc,xbmcgui

try: from sqlite3 import dbapi2 as database
except: from pysqlite2 import dbapi2 as database

from resources.lib.modules import debrid
from resources.lib.modules import cache
from resources.lib.modules import metacache
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules import regex
from resources.lib.modules import trailer
from resources.lib.modules import workers
from resources.lib.modules import youtube
from resources.lib.modules import views
from resources.lib.modules import trakt
from resources.lib.modules import log_utils
from resources.lib.modules import dom_parser2

addon_id            = 'plugin.video.bennu'
AddonTitle          = 'bennu'
PARENTAL_FOLDER     = xbmc.translatePath(os.path.join('special://home/userdata/addon_data/' + addon_id , 'parental'))
PARENTAL_FILE       = xbmc.translatePath(os.path.join(PARENTAL_FOLDER , 'control.txt'))
tm_img_link = 'https://image.tmdb.org/t/p/w%s%s'

class indexer:
    def __init__(self):
        self.list = [] ; self.hash = []

    def root(self):
        cache.cache_version_check()
        try:
            regex.clear()
            url = base64.b64decode('aHR0cHM6Ly9wYXN0ZWJpbi5jb20vcmF3L2h1QTVaSFhV')
            self.list = self.bennu_list(url, enc=True)
            for i in self.list: i.update({'content': 'addons'})
            self.addDirectory(self.list, cache=False)
            return self.list
        except:
            pass

    def get(self, url):
        try:
            self.list = self.bennu_list(url)
            self.worker()
            self.addDirectory(self.list)
            return self.list
        except:
            pass

    def getq(self, url):
        try:
            self.list = self.bennu_list(url)
            self.worker()
            self.addDirectory(self.list, queue=True)
            return self.list
        except:
            pass


    def getx(self, url, worker=False):
        try:
            r, x = re.findall('(.+?)\|regex=(.+?)$', url)[0]
            x = regex.fetch(x)
            r += urllib.unquote_plus(x)
            url = regex.resolve(r)
            self.list = self.bennu_list('', result=url)
            if worker == True: self.worker()
            self.addDirectory(self.list)
            return self.list
        except:
            pass

    def getimdb(self, url):
        try:
            self.list = self.imdb_list(url)
            self.addDirectory(self.list)
            return self.list
        except:
            pass

    def gettrakt(self, url):
        try:
            self.list = self.trakt_list(url)
            self.addDirectory(self.list)
            return self.list
        except:
            pass
           
    def getrotten(self, url):
        try:
            self.list = self.rotten_list(url)
            self.addDirectory(self.list)
            return self.list
        except:
            pass
            
    def developer(self):
        try:
            url = os.path.join(control.dataPath, 'testings.xml')
            f = control.openFile(url) ; result = f.read() ; f.close()
            self.list = self.bennu_list('', result=result)
            for i in self.list: i.update({'content': 'videos'})
            self.addDirectory(self.list)
            return self.list
        except:
            pass
            
    def private(self):
            skip_m = False
            pb_list = []
            pb_list.append(control.setting('pb_private'))
            pb_list.append(control.setting('pb_private2'))
            pb_list.append(control.setting('pb_private3'))
            pb_list.append(control.setting('pb_private4'))
            pb_list.append(control.setting('pb_private5'))

            pb_list = [base64.b64decode('aHR0cHM6Ly9wYXN0ZWJpbi5jb20vcmF3LyVz') % i for i in pb_list if not i == '' and len(i) == 8]
            
            if len(pb_list) == 0: quit()
            elif len(pb_list) == 1: skip_m = True
                    
            pattern = '''%s''' % base64.b64decode('W2F0PGlzbWw+ZW5dezEwfShbXjxdKylbYVwvdDxpc21sPmVuezExfV0=')

            if skip_m:
                result = client.request(pb_list[0])
                try:
                    n = re.findall(pattern, result)[0]
                except:
                    result = self.aes_dec(result)
            else:
                namelst = []
                for i in pb_list:
                    try:
                        n = None
                        result = client.request(i)
                        pattern = '''%s''' % base64.b64decode('W2F0PGlzbWw+ZW5dezEwfShbXjxdKylbYVwvdDxpc21sPmVuezExfV0=')
                        
                        try:
                            n = re.findall(pattern, result)[0]
                        except:
                            result = self.aes_dec(result)
                            n = re.findall(pattern, result)[0]
                        if n: namelst += [(n, i)]
                    except: pass
                
                dialog_list = []
                for i, n in namelst: dialog_list += [(n, i)]

                select = control.selectDialog([i[1] for i in dialog_list], control.addonInfo('name'))

                if select == -1: return False
                else: result = client.request(dialog_list[select][0])
                    
            self.list = self.bennu_list('', result=result)
            for i in self.list: i.update({'content': 'videos'})
            self.addDirectory(self.list)
            return self.list

    def aes_dec(self, result):
        try:
            from resources.lib.modules import pyaes
            aes = pyaes.AESModeOfOperationOFB(control.key, iv=control.iv)
            result = aes.decrypt(result.decode('string-escape'))
            return result
        except:
            return result
        
    def parental_controls(self):
        
        dialog = xbmcgui.Dialog()
        
        if os.path.isfile(PARENTAL_FILE):
            choice = dialog.yesno(AddonTitle,'Would you like to disable parental controls?')
            if choice:
                vq = client._get_keyboard( heading="Please Enter Your Password" , hidden=True)
                if ( not vq ): 
                    dialog.ok(AddonTitle,"Sorry, no password was entered.")
                    quit()
                pass_one = hashlib.sha256(vq).hexdigest()

                remove_me = 0
                vers = open(PARENTAL_FILE, "r")
                regex = re.compile(r'<password>(.+?)</password>')
                for line in vers:
                    file = regex.findall(line)
                    for password in file:
                        if not password == pass_one:
                            dialog.ok(AddonTitle,"Sorry, the password you entered was incorrect.")
                            quit()
                        else:
                            remove_me = 1
                            dialog.ok(AddonTitle,"Parental controls have been disabled.")
                            
                if remove_me == 1:
                    vers.close()
                    os.remove(PARENTAL_FILE)

            else: quit()

        else:
            choice = dialog.yesno(AddonTitle,'To use the ADULT section you must set a password.','Would you like to set a password now?')
            if choice:
                vq = client._get_keyboard( heading="Please Set Password" , hidden=True)
                if ( not vq ):
                    dialog.ok(AddonTitle,"Sorry, no password was entered.")
                    quit()
                pass_one = vq

                vq = client._get_keyboard( heading="Please Confirm Your Password" , hidden=True)
                if ( not vq ):
                    dialog.ok(AddonTitle,"Sorry, no password was entered.")
                    quit()
                pass_two = vq
                    
                if not os.path.exists(PARENTAL_FILE):
                    if not os.path.exists(PARENTAL_FOLDER):
                        os.makedirs(PARENTAL_FOLDER)
                    open(PARENTAL_FILE, 'w')

                if pass_one == pass_two:
                    writeme = hashlib.sha256(pass_one).hexdigest()
                    f = open(PARENTAL_FILE,'w')
                    f.write('<password>'+str(writeme)+'</password>')
                    f.close()
                    dialog.ok(AddonTitle,'Your password has been set and parental controls have been enabled.')
                    xbmc.executebuiltin("Container.Refresh")
                else:
                    dialog.ok(AddonTitle,'The passwords do not match, please try again.')
                    quit()

    def youtube(self, url, action):
        try:
            key = trailer.trailer().key_link.split('=', 1)[-1]

            if 'PlaylistTuner' in action:
                self.list = cache.get(youtube.youtube(key=key).playlist, 1, url)
            elif 'Playlist' in action:
                self.list = cache.get(youtube.youtube(key=key).playlist, 1, url, True)
            elif 'ChannelTuner' in action:
                self.list = cache.get(youtube.youtube(key=key).videos, 1, url)
            elif 'Channel' in action:
                self.list = cache.get(youtube.youtube(key=key).videos, 1, url, True)

            if 'Tuner' in action:
                for i in self.list: i.update({'name': i['title'], 'poster': i['image'], 'action': 'plugin', 'folder': False})
                if 'Tuner2' in action: self.list = sorted(self.list, key=lambda x: random.random())
                self.addDirectory(self.list, queue=True)
            else:
                for i in self.list: i.update({'name': i['title'], 'poster': i['image'], 'nextaction': action, 'action': 'play', 'folder': False})
                self.addDirectory(self.list)

            return self.list
        except:
            pass


    def tvtuner(self, url):
        try:
            preset = re.findall('<preset>(.+?)</preset>', url)[0]

            today = ((datetime.datetime.utcnow() - datetime.timedelta(hours = 5))).strftime('%Y-%m-%d')
            today = int(re.sub('[^0-9]', '', str(today)))

            url, imdb, tvdb, tvshowtitle, year, thumbnail, fanart = re.findall('<url>(.+?)</url>', url)[0], re.findall('<imdb>(.+?)</imdb>', url)[0], re.findall('<tvdb>(.+?)</tvdb>', url)[0], re.findall('<tvshowtitle>(.+?)</tvshowtitle>', url)[0], re.findall('<year>(.+?)</year>', url)[0], re.findall('<thumbnail>(.+?)</thumbnail>', url)[0], re.findall('<fanart>(.+?)</fanart>', url)[0]

            tvm = client.request('http://api.tvmaze.com/lookup/shows?thetvdb=%s' % tvdb)
            if tvm  == None: tvm = client.request('http://api.tvmaze.com/lookup/shows?imdb=%s' % imdb)
            tvm ='http://api.tvmaze.com/shows/%s/episodes' % str(json.loads(tvm).get('id'))
            items = json.loads(client.request(tvm))
            items = [(str(i.get('season')), str(i.get('number')), i.get('name').strip(), i.get('airdate')) for i in items]

            if preset == 'tvtuner':
                choice = random.choice(items)
                items = items[items.index(choice):] + items[:items.index(choice)]
                items = items[:100]

            result = ''

            for i in items:
                try:
                    if int(re.sub('[^0-9]', '', str(i[3]))) > today: raise Exception()
                    result += '<item><title> %01dx%02d . %s</title><meta><content>episode</content><imdb>%s</imdb><tvdb>%s</tvdb><tvshowtitle>%s</tvshowtitle><year>%s</year><title>%s</title><premiered>%s</premiered><season>%01d</season><episode>%01d</episode></meta><link><sublink>search</sublink><sublink>searchsd</sublink></link><thumbnail>%s</thumbnail><fanart>%s</fanart></item>' % (int(i[0]), int(i[1]), i[2], imdb, tvdb, tvshowtitle, year, i[2], i[3], int(i[0]), int(i[1]), thumbnail, fanart)
                except:
                    pass

            result = re.sub(r'[^\x00-\x7F]+', ' ', result)

            if preset == 'tvtuner':
                result = result.replace('<sublink>searchsd</sublink>', '')

            self.list = self.bennu_list('', result=result)

            if preset == 'tvtuner':
                self.addDirectory(self.list, queue=True)
            else:
                self.worker()
                self.addDirectory(self.list)
        except:
            pass

    def search(self, url):
        try:
            mark = False
            if (url == None or url == ''):
                self.list = [{'name': 30702, 'action': 'addSearch'}]
                self.list += [{'name': 30703, 'action': 'delSearch'}]
            else:
                if '|SECTION|' in url: mark = url.split('|SECTION|')[0]
                self.list = [{'name': 30702, 'url': url, 'action': 'addSearch'}]
                self.list += [{'name': 30703, 'action': 'delSearch'}]

            try:
                def search(): return
                query = cache.get(search, 600000000, table='rel_srch')

                for url in query:
                    
                    if mark != False:
                        if mark in url:
                            name = url.split('|SPLITER|')[0]
                            try: self.list += [{'name': '%s...' % name, 'url': url, 'action': 'addSearch'}]
                            except: pass
                    else:
                        if not '|SPLITER|' in url:
                            try: self.list += [{'name': '%s...' % url, 'url': url, 'action': 'addSearch'}]
                            except: pass
            except:
                pass

            self.addDirectory(self.list)
            return self.list
        except:
            pass


    def delSearch(self):
        try:
            cache.clear('rel_srch')
            control.refresh()
        except:
            pass


    def addSearch(self, url):
    
            try:
                skip = 0
                if '|SPLITER|' in url:
                    keep = url
                    url,matcher = url.split('|SPLITER|')
                    skip = 1
                    section = 1
                elif '|SECTION|' in url:
                    matcher = url.replace('|SECTION|','')
                    section = 1
                else: 
                    section = 0
            except: section = 0

            link = 'https://pastebin.com/raw/A2D1mRSE'

            if skip == 0:
                if section == 1:
                    keyboard = control.keyboard('', control.lang(30702).encode('utf-8'))
                    keyboard.doModal()
                    if not (keyboard.isConfirmed()): return
                    url = keyboard.getText()
                    keep = url + '|SPLITER|' + matcher
                else:
                    if (url == None or url == ''):
                        keyboard = control.keyboard('', control.lang(30702).encode('utf-8'))
                        keyboard.doModal()
                        if not (keyboard.isConfirmed()): return
                        url = keyboard.getText()

            if (url == None or url == ''): return

            if section == 1:
                input = keep
            else: 
                input = url
            def search(): return [input]
            query = cache.get(search, 600000000, table='rel_srch')

            def search(): return [x for y,x in enumerate((query + [input])) if x not in (query + [input])[:y]]
            cache.get(search, 0, table='rel_srch')

            links = client.request(link)
            links = re.findall('<link>(.+?)</link>', links)
            if section == 0: links = [i for i in links if str(i).startswith('http')]
            else: links = [i for i in links if str(i).startswith('http') and matcher.lower() in str(i).lower()]
            
            self.list = [] ; threads = [] 
            for link in links: threads.append(workers.Thread(self.bennu_list, link))
            [i.start() for i in threads] ; [i.join() for i in threads]

            
            self.list = [i for i in self.list if url.lower() in i['name'].lower()]

            for i in self.list:
                try:
                    name = ''
                    if not i['vip'] in ['bennu TV']: name += '[B]%s[/B] | ' % i['vip'].upper()
                    name += i['name']
                    i.update({'name' : name})
                except:
                    pass

            for i in self.list: i.update({'content': 'videos'})
            self.addDirectory(self.list)

    def rotten_list(self, url):
        
        c = cache.get(client.request, 72, url)
        
        try:
            pattern = '''\<a\s*href=['"]([^'"]+)['"]\>\s*Next\s*\<\/a\>'''
            np = re.findall(pattern, c)[0]
            self.list.append({'nextaction': 'rotten_list', 'next': np})
        except: pass
        
        u = dom_parser2.parse_dom(c, 'div', {'class': 'gray-movie-block'})
        if u:
            r = [(dom_parser2.parse_dom(i, 'a', req='href'), \
                  dom_parser2.parse_dom(i, 'span', {'class': 'subtle'}), \
                  dom_parser2.parse_dom(i, 'span', {'class': 'tMeterScore'}), \
                  dom_parser2.parse_dom(i, 'img', req='src'), \
                  dom_parser2.parse_dom(i, 'p')) for i in u]
            r = [(i[0][0].content, i[1][0].content.replace('(','').replace(')',''), i[2][0].content, i[3][0].attrs['src'], i[4][0].content) for i in r if i[0] and i[1] and i[2] and i[3] and i[4]]
        else:
            u = dom_parser2.parse_dom(c, 'div', {'id': re.compile('row-index-.+?')})
            r = [(dom_parser2.parse_dom(i, 'a', req='href'), \
                  dom_parser2.parse_dom(i, 'span', {'class': 'subtle'}), \
                  dom_parser2.parse_dom(i, 'span', {'class': 'tMeterScore'}), \
                  dom_parser2.parse_dom(i, 'img', req='src'), \
                  dom_parser2.parse_dom(i, 'div', {'class': ['info','synopsis']})) for i in u]
            r = [(i[0][1].content, i[1][0].content.replace('(','').replace(')',''), i[2][0].content, i[3][0].attrs['src'], re.sub('<.+?>','',i[4][0].content)) for i in r if i[0] and i[1] and i[2] and i[3] and i[4]]

        if r:
            for i in r:
                try:
                    name = '%s (%s)' % (client.replaceHTMLCodes(client.removeNonAscii(i[0].encode('utf-8'))), i[1])
                    original_name = client.replaceHTMLCodes(client.removeNonAscii(i[0].encode('utf-8')))

                    url = '<sublink><preset>search</preset>        <content>movie</content>        <imdb>%s</imdb>        <title>%s</title>        <year>%s</year>        </sublink>        <sublink><preset>searchsd</preset>        <content>movie</content>        <imdb>%s</imdb>        <title>%s</title>        <year>%s</year>        </sublink>        <thumbnail>%s</thumbnail>' % ('0', original_name, i[1], '0', original_name, i[1], i[3])
                    self.list.append({'name': name, 'vip': '0', 'url': url, 'action': 'play', 'folder': False, 'poster': i[3], 'banner': '0', 'fanart': control.addonInfo('fanart'), 'content': 'movies', 'imdb': '0', 'tvdb': '0', 'tmdb': '0', 'title': original_name, 'originaltitle': original_name, 'tvshowtitle': '0', 'year': i[1], 'premiered': '0', 'season': '0', 'episode': '0', 'worker': '0', 'rating': i[2], 'plot': client.replaceHTMLCodes(i[4])})
                except: log_utils.log('Scraping Error: Could not add %s to directory.' % str(original_name), log_utils.LOGERROR)
            return self.list

    def trakt_list(self, url):
        
        c = cache.get(client.request, 72, url)
        
        u = dom_parser2.parse_dom(c, 'div', {'class': 'grid-item'})
        r = [(i.attrs['data-runtime'], \
              dom_parser2.parse_dom(i, 'img', {'class': 'real'})) for i in u]
        r = [(i[1][0].attrs['title'], re.findall('\(([^\)]+)', 
              i[1][0].attrs['title'])[0] if '(' in i[1][0].attrs['title'] else '0',
              i[0], i[1][0].attrs['data-original']) for i in r if i[0] and i[1]]
              
        if r:
            for i in r:
                try:
                    name = client.replaceHTMLCodes(i[0])
                    original_name = re.sub('\s+\(\d+\)', '', name)
                    try: duration = str(int(i[2]) * 60)
                    except: duration = 0
                    url = '<sublink><preset>search</preset>        <content>movie</content>        <imdb>%s</imdb>        <title>%s</title>        <year>%s</year>        </sublink>        <sublink><preset>searchsd</preset>        <content>movie</content>        <imdb>%s</imdb>        <title>%s</title>        <year>%s</year>        </sublink>        <thumbnail>%s</thumbnail>' % ('0', original_name, i[1], '0', original_name, i[1], i[3])
                    self.list.append({'name': name, 'vip': '0', 'url': url, 'action': 'play', 'folder': False, 'poster': i[3], 'banner': '0', 'fanart': control.addonInfo('fanart'), 'content': 'movies', 'imdb': '0', 'tvdb': '0', 'tmdb': '0', 'title': original_name, 'originaltitle': original_name, 'tvshowtitle': '0', 'year': i[1], 'premiered': '0', 'season': '0', 'episode': '0', 'worker': '0', 'duration': duration})
                except: log_utils.log('Scraping Error: Could not add %s to directory.' % str(original_name), log_utils.LOGERROR)
            return self.list
            
    def imdb_list(self, url):
        
        if url.startswith('http'): i_url = url
        else: i_url = 'http://www.imdb.com/list/%s/' % url
        c = cache.get(client.request, 72, i_url)

        try:
            pattern = '''<meta\s*property=['"]og\:url['"]\s*content=['"]([^'"]+)'''
            base_url = re.findall(pattern, c)[0]
            pattern = '''<a\s*href=['"]([^'"]+)['"]>Next\&'''
            np = re.findall(pattern, c)[0]
            if not np.startswith('http'): np = urlparse.urljoin(base_url, np)
            self.list.append({'nextaction': 'imdb_list', 'next': np})
        except: pass
        
        u = dom_parser2.parse_dom(c, 'div', {'class': 'list_item'})
        r = [(dom_parser2.parse_dom(i, 'div', {'class': 'hover-over-image'}), \
              dom_parser2.parse_dom(i, 'a', req='href'), \
              dom_parser2.parse_dom(i, 'span', {'class': 'year_type'}), \
              dom_parser2.parse_dom(i, 'div', {'class': 'item_description'}), \
              dom_parser2.parse_dom(i, 'img', req='src'), \
              dom_parser2.parse_dom(i, 'span', {'class': 'value'})) \
              for i in u]
        r = [(i[0][0].attrs['data-const'], i[1][1].content,
              re.findall('(\d+)', i[2][0].content)[0], re.sub('<.+?>', '', i[3][0].content),
              i[4][0].attrs['loadlate'] if 'loadlate=' in i[4][0].content else i[4][-1].attrs['src'], \
              i[5][0].content if i[5][0].content else '0.0', str(int(re.findall('\((\d+)\s*mins', i[3][0].content)[0]) * 60)) \
              for i in r if i[0] and i[1] and i[2] and i[3] and i[4] and i[5]]
        
        if r:
            for i in r:
                try:
                    name = '%s (%s)' % (client.replaceHTMLCodes(i[1]), i[2])
                    original_name = client.replaceHTMLCodes(i[1])
                    url = '<sublink><preset>search</preset>        <content>movie</content>        <imdb>%s</imdb>        <title>%s</title>        <year>%s</year>        </sublink>        <sublink><preset>searchsd</preset>        <content>movie</content>        <imdb>%s</imdb>        <title>%s</title>        <year>%s</year>        </sublink>        <thumbnail>%s</thumbnail>' % (i[0], original_name, i[2], i[0], original_name, i[2], i[4])
                    self.list.append({'name': name, 'vip': '0', 'url': url, 'action': 'play', 'folder': False, 'poster': i[4], 'banner': '0', 'fanart': control.addonInfo('fanart'), 'content': 'movies', 'imdb': i[0], 'tvdb': '0', 'tmdb': '0', 'title': original_name, 'originaltitle': original_name, 'tvshowtitle': '0', 'year': i[2], 'premiered': '0', 'season': '0', 'episode': '0', 'worker': '0', 'plot': i[3], 'rating': i[5], 'duration': i[6]})
                except: log_utils.log('Scraping Error: Could not add %s to directory.' % str(original_name), log_utils.LOGERROR)
            return self.list

    def bennu_list(self, url, result=None, enc=False):
        checks = ['D5ZdEKZg','5yETXEUA']
        if any(x in url for x in checks): 
            dialog = xbmcgui.Dialog()
            if not os.path.isfile(PARENTAL_FILE):
                self.parental_controls()
                quit()
            else:
                vq = client._get_keyboard( heading="Please Enter Your Password" , hidden=True)

                if ( not vq ): 
                    dialog.ok(AddonTitle,"Sorry, no password was entered.")
                    quit()
            
                pass_one = hashlib.sha256(vq).hexdigest()

                vers = open(PARENTAL_FILE, "r")
                regex2 = re.compile(r'<password>(.+?)</password>')
                for line in vers:
                    file = regex2.findall(line)
                    for password in file:
                        if not password == pass_one:
                            dialog.ok(AddonTitle,"Sorry, the password you entered was incorrect.")
                            quit()

        try:
            
            if result == None: result = cache.get(client.request, 1, url)
            
            checks = ['<item>','<dir>','<plugin>','<info>','<name>','<link>']
            if not any(x in result for x in checks): result = self.aes_dec(result)
            elif enc == True: result = self.aes_dec(result)

            if result.strip().startswith('#EXTM3U') and '#EXTINF' in result:
                result = re.compile('#EXTINF:.+?\,(.+?)\n(.+?)\n', re.MULTILINE|re.DOTALL).findall(result)
                result = ['<item><title>%s</title><link>%s</link></item>' % (i[0], i[1]) for i in result]
                result = ''.join(result)

            try: r = base64.b64decode(result)
            except: r = ''
            if '</link>' in r: result = r

            result = str(result)

            info = result.split('<item>')[0].split('<dir>')[0]

            try: vip = re.findall('<poster>(.+?)</poster>', info)[0]
            except: vip = '0'

            try: image = re.findall('<thumbnail>(.+?)</thumbnail>', info)[0]
            except: image = '0'

            try: fanart = re.findall('<fanart>(.+?)</fanart>', info)[0]
            except: fanart = '0'

            items = re.compile('((?:<item>.+?</item>|<dir>.+?</dir>|<plugin>.+?</plugin>|<info>.+?</info>|<name>[^<]+</name><link>[^<]+</link><thumbnail>[^<]+</thumbnail><mode>[^<]+</mode>|<name>[^<]+</name><link>[^<]+</link><thumbnail>[^<]+</thumbnail><date>[^<]+</date>))', re.MULTILINE|re.DOTALL).findall(result)
        except:
            return

        for item in items:
            try:
                regdata = re.compile('(<regex>.+?</regex>)', re.MULTILINE|re.DOTALL).findall(item)
                regdata = ''.join(regdata)
                reglist = re.compile('(<listrepeat>.+?</listrepeat>)', re.MULTILINE|re.DOTALL).findall(regdata)
                regdata = urllib.quote_plus(regdata)

                reghash = hashlib.md5()
                for i in regdata: reghash.update(str(i))
                reghash = str(reghash.hexdigest())

                item = item.replace('\r','').replace('\n','').replace('\t','').replace('&nbsp;','')
                item = re.sub('<regex>.+?</regex>','', item)
                item = re.sub('<sublink></sublink>|<sublink\s+name=(?:\'|\").*?(?:\'|\")></sublink>','', item)
                item = re.sub('<link></link>','', item)

                name = re.sub('<meta>.+?</meta>','', item)
                try: name = re.findall('<title>(.+?)</title>', name)[0]
                except: name = re.findall('<name>(.+?)</name>', name)[0]

                try: date = re.findall('<date>(.+?)</date>', item)[0]
                except: date = ''
                if re.search(r'\d+', date): name += ' [COLOR red] Updated %s[/COLOR]' % date

                try: image2 = re.findall('<thumbnail>(.+?)</thumbnail>', item)[0]
                except: image2 = image

                try: fanart2 = re.findall('<fanart>(.+?)</fanart>', item)[0]
                except: fanart2 = fanart

                try: meta = re.findall('<meta>(.+?)</meta>', item)[0]
                except: meta = '0'
                
                try: use_worker = re.findall('<worker>(.+?)</worker>', item)[0]
                except: use_worker = '0'

                try: url = re.findall('<link>(.+?)</link>', item)[0]
                except: url = '0'
                url = url.replace('>search<', '><preset>search</preset>%s<' % meta)
                url = '<preset>search</preset>%s' % meta if url == 'search' else url
                url = url.replace('>searchsd<', '><preset>searchsd</preset>%s<' % meta)
                url = '<preset>searchsd</preset>%s' % meta if url == 'searchsd' else url
                url = re.sub('<sublink></sublink>|<sublink\s+name=(?:\'|\").*?(?:\'|\")></sublink>','', url)

                if item.startswith('<item>'): action = 'play'
                elif item.startswith('<plugin>'): action = 'plugin'
                elif item.startswith('<info>') or url == '0': action = '0'
                else: action = 'directory'
                if action == 'play' and reglist: action = 'xdirectory'

                if not regdata == '':
                    self.hash.append({'regex': reghash, 'response': regdata})
                    url += '|regex=%s' % reghash

                if action in ['directory', 'xdirectory', 'plugin']:
                    folder = True
                else:
                    folder = False

                try: content = re.findall('<content>(.+?)</content>', meta)[0]
                except: content = '0'
                if content == '0': 
                    try: content = re.findall('<content>(.+?)</content>', item)[0]
                    except: content = '0'
                if not content == '0': content += 's'

                if 'tvshow' in content and not url.strip().endswith('.xml'):
                    url = '<preset>tvindexer</preset><url>%s</url><thumbnail>%s</thumbnail><fanart>%s</fanart>%s' % (url, image2, fanart2, meta)
                    action = 'tvtuner'

                if 'tvtuner' in content and not url.strip().endswith('.xml'):
                    url = '<preset>tvtuner</preset><url>%s</url><thumbnail>%s</thumbnail><fanart>%s</fanart>%s' % (url, image2, fanart2, meta)
                    action = 'tvtuner'

                try: imdb_list = re.findall('<imdb_list>(.+?)</imdb_list>', item)[0]
                except: imdb_list = False
                if imdb_list:
                    action = 'imdb_list'; url = imdb_list; folder = True

                try: trakt_list = re.findall('<trakt_list>(.+?)</trakt_list>', item)[0]
                except: trakt_list = False
                if trakt_list:
                    action = 'trakt_list'; url = trakt_list; folder = True
                    
                try: rotten_list = re.findall('<rotten_list>(.+?)</rotten_list>', item)[0]
                except: rotten_list = False
                if rotten_list:
                    action = 'rotten_list'; url = rotten_list; folder = True
                    
                try: yt_channel = re.findall('<yt_channel>(.+?)</yt_channel>', item)[0]
                except: yt_channel = False
                if yt_channel:
                    action = 'youtubeChannel'; url = yt_channel; folder = True
                    
                try: imdb = re.findall('<imdb>(.+?)</imdb>', meta)[0]
                except: imdb = '0'

                try: tvdb = re.findall('<tvdb>(.+?)</tvdb>', meta)[0]
                except: tvdb = '0'

                try: tvshowtitle = re.findall('<tvshowtitle>(.+?)</tvshowtitle>', meta)[0]
                except: tvshowtitle = '0'

                try: title = re.findall('<title>(.+?)</title>', meta)[0]
                except: title = '0'

                if title == '0' and not tvshowtitle == '0': title = tvshowtitle

                try: year = re.findall('<year>(.+?)</year>', meta)[0]
                except: year = '0'

                try: premiered = re.findall('<premiered>(.+?)</premiered>', meta)[0]
                except: premiered = '0'

                try: season = re.findall('<season>(.+?)</season>', meta)[0]
                except: season = '0'

                try: episode = re.findall('<episode>(.+?)</episode>', meta)[0]
                except: episode = '0'

                self.list.append({'name': name, 'vip': vip, 'url': url, 'action': action, 'folder': folder, 'poster': image2, 'banner': '0', 'fanart': fanart2, 'content': content, 'imdb': imdb, 'tvdb': tvdb, 'tmdb': '0', 'title': title, 'originaltitle': title, 'tvshowtitle': tvshowtitle, 'year': year, 'premiered': premiered, 'season': season, 'episode': episode, 'worker': use_worker})
            except:
                pass

        regex.insert(self.hash)

        return self.list

    def worker(self):
    
        if not control.setting('metadata') == 'true': return

        self.tvmaze_info_link = 'http://api.tvmaze.com/lookup/shows?thetvdb=%s'

        self.lang = 'en'
        self.user = ''

        self.meta = []
        total = len(self.list)
        if total == 0: return
     
        self.fanart_tv_art_link = 'http://webservice.fanart.tv/v3/movies/%s'     
        self.fanart_tv_headers = {'api-key': 'ZDY5NTRkYTk2Yzg4ODFlMzdjY2RkMmQyNTlmYjk1MzQ='.decode('base64')}

        for i in range(0, total): self.list[i].update({'metacache': False})
        
        self.list = metacache.fetch(self.list, self.lang, self.user)
        
        pDialog = xbmcgui.DialogProgressBG()
        pDialog.create('MetaData Progress', '')
        pDialog.update(0, 'MetaData Progress', 'Retrieving MetaData Information')
        import time
        start = time.time()
        for r in range(0, total, 50):
            threads = []
            percent = int( ( (r) / float(total) ) * 100)
            pDialog.update(percent, 'MetaData Progress', 'Retrieving MetaData Information')
            for i in range(r, r+50):
                if i <= total: threads.append(workers.Thread(self.movie_info, i))
                if i <= total: threads.append(workers.Thread(self.tv_info, i))
            [i.start() for i in threads]
            [i.join() for i in threads]
            
            if self.meta: metacache.insert(self.meta)

        pDialog.close()

        try:
            self.list = metacache.local(self.list, tm_img_link, 'poster3', 'fanart2')
            for i in self.list: i.update({'clearlogo': '0', 'clearart': '0'})
        except: pass
        
    def movie_info(self, i):
        try:
            if self.list[i]['metacache'] == True: raise Exception()

            if not self.list[i]['content'] == 'movies': raise Exception()

            imdb = self.list[i]['imdb']
            if imdb == '0': raise Exception()

            item = trakt.getMovieSummary(imdb)

            if 'Error' in item and 'incorrect imdb' in item['Error'].lower():
                return self.meta.append({'imdb': imdb, 'tmdb': '0', 'tvdb': '0', 'lang': self.lang, 'user': self.user, 'item': {'code': '0'}})

            title = item.get('title')
            title = client.replaceHTMLCodes(title)

            originaltitle = title

            year = item.get('year', 0)
            year = re.sub('[^0-9]', '', str(year))

            imdb = item.get('ids', {}).get('imdb', '0')
            imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))

            tmdb = str(item.get('ids', {}).get('tmdb', 0))

            premiered = item.get('released', '0')
            try: premiered = re.compile('(\d{4}-\d{2}-\d{2})').findall(premiered)[0]
            except: premiered = '0'

            genre = item.get('genres', [])
            genre = [x.title() for x in genre]
            genre = ' / '.join(genre).strip()
            if not genre: genre = '0'

            duration = str(item.get('runtime', 0))
            duration = str(int(duration) * 60)

            rating = item.get('rating', '0')
            if not rating or rating == '0.0': rating = '0'

            votes = item.get('votes', '0')
            try: votes = str(format(int(votes), ',d'))
            except: pass

            mpaa = item.get('certification', '0')
            if not mpaa: mpaa = '0'

            tagline = item.get('tagline', '0')

            plot = item.get('overview', '0')

            people = trakt.getPeople(imdb, 'movies')

            director = writer = ''
            if 'crew' in people and 'directing' in people['crew']:
                director = ', '.join([director['person']['name'] for director in people['crew']['directing'] if director['job'].lower() == 'director'])
            if 'crew' in people and 'writing' in people['crew']:
                writer = ', '.join([writer['person']['name'] for writer in people['crew']['writing'] if writer['job'].lower() in ['writer', 'screenplay', 'author']])

            cast = []
            for person in people.get('cast', []):
                cast.append({'name': person['person']['name'], 'role': person['character']})
            cast = [(person['name'], person['role']) for person in cast]

            try:
                if self.lang == 'en' or self.lang not in item.get('available_translations', [self.lang]): raise Exception()

                trans_item = trakt.getMovieTranslation(imdb, self.lang, full=True)

                title = trans_item.get('title') or title
                tagline = trans_item.get('tagline') or tagline
                plot = trans_item.get('overview') or plot
            except:
                pass

            try:
                artmeta = True
                #if self.fanart_tv_user == '': raise Exception()           
                art = client.request(self.fanart_tv_art_link % imdb, headers=self.fanart_tv_headers, timeout='10', error=True)
                try: art = json.loads(art)
                except: artmeta = False
            except:
                pass
                
            try:
                poster2 = art['movieposter']
                poster2 = [x for x in poster2 if x.get('lang') == self.lang][::-1] + [x for x in poster2 if x.get('lang') == 'en'][::-1] + [x for x in poster2 if x.get('lang') in ['00', '']][::-1]
                poster2 = poster2[0]['url'].encode('utf-8')
            except:
                poster2 = '0'

            try:
                if 'moviebackground' in art: fanart = art['moviebackground']
                else: fanart = art['moviethumb']
                fanart = [x for x in fanart if x.get('lang') == self.lang][::-1] + [x for x in fanart if x.get('lang') == 'en'][::-1] + [x for x in fanart if x.get('lang') in ['00', '']][::-1]
                fanart = fanart[0]['url'].encode('utf-8')
            except:
                fanart = '0'

            try:
                banner = art['moviebanner']
                banner = [x for x in banner if x.get('lang') == self.lang][::-1] + [x for x in banner if x.get('lang') == 'en'][::-1] + [x for x in banner if x.get('lang') in ['00', '']][::-1]
                banner = banner[0]['url'].encode('utf-8')
            except:
                banner = '0'

            try:
                if 'hdmovielogo' in art: clearlogo = art['hdmovielogo']
                else: clearlogo = art['clearlogo']
                clearlogo = [x for x in clearlogo if x.get('lang') == self.lang][::-1] + [x for x in clearlogo if x.get('lang') == 'en'][::-1] + [x for x in clearlogo if x.get('lang') in ['00', '']][::-1]
                clearlogo = clearlogo[0]['url'].encode('utf-8')
            except:
                clearlogo = '0'

            try:
                if 'hdmovieclearart' in art: clearart = art['hdmovieclearart']
                else: clearart = art['clearart']
                clearart = [x for x in clearart if x.get('lang') == self.lang][::-1] + [x for x in clearart if x.get('lang') == 'en'][::-1] + [x for x in clearart if x.get('lang') in ['00', '']][::-1]
                clearart = clearart[0]['url'].encode('utf-8')
            except:
                clearart = '0'

            try:
                self.tm_user = control.setting('tm.user')
                self.tm_art_link = 'http://api.themoviedb.org/3/movie/%s/images?api_key=%s&language=en-US&include_image_language=en,%s,null' % ('%s', self.tm_user, self.lang)
                if self.tm_user == '': raise Exception()
                art2 = client.request(self.tm_art_link % imdb, timeout='10', error=True)
                art2 = json.loads(art2)
            except:
                pass

            try:
                poster3 = art2['posters']
                poster3 = [x for x in poster3 if x.get('iso_639_1') == self.lang] + [x for x in poster3 if x.get('iso_639_1') == 'en'] + [x for x in poster3 if x.get('iso_639_1') not in [self.lang, 'en']]
                poster3 = [(x['width'], x['file_path']) for x in poster3]
                poster3 = [(x[0], x[1]) if x[0] < 300 else ('300', x[1]) for x in poster3]
                poster3 = tm_img_link % poster3[0]
                poster3 = poster3.encode('utf-8')
            except:
                poster3 = '0'

            try:
                fanart2 = art2['backdrops']
                fanart2 = [x for x in fanart2 if x.get('iso_639_1') == self.lang] + [x for x in fanart2 if x.get('iso_639_1') == 'en'] + [x for x in fanart2 if x.get('iso_639_1') not in [self.lang, 'en']]
                fanart2 = [x for x in fanart2 if x.get('width') == 3840] + [x for x in fanart2 if x.get('width') < 3840]
                fanart2 = [(x['width'], x['file_path']) for x in fanart2]
                fanart2 = [(x[0], x[1]) if x[0] < 1280 else ('1280', x[1]) for x in fanart2]
                fanart2 = tm_img_link % fanart2[0]
                fanart2 = fanart2.encode('utf-8')
            except:
                fanart2 = '0'

            item = {'title': title, 'originaltitle': originaltitle, 'year': year, 'imdb': imdb, 'tmdb': tmdb, 'poster': '0', 'poster2': poster2, 'poster3': poster3, 'banner': banner, 'fanart': fanart, 'fanart2': fanart2, 'clearlogo': clearlogo, 'clearart': clearart, 'premiered': premiered, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'director': director, 'writer': writer, 'cast': cast, 'plot': plot, 'tagline': tagline}
            item = dict((k,v) for k, v in item.iteritems() if not v == '0')
            self.list[i].update(item)

            if artmeta == False: raise Exception()

            meta = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'lang': self.lang, 'user': self.user, 'item': item}
            self.meta.append(meta)
        except:
            pass    
           
    def tv_info(self, i):
        try:
            if self.list[i]['metacache'] == True: raise Exception()

            if not self.list[i]['content'] in ['tvshows', 'seasons', 'episodes']: raise Exception()

            tvdb = self.list[i]['tvdb']
            if tvdb == '0': raise Exception()

            url = self.tvmaze_info_link % tvdb

            item = client.request(url, output='extended', error=True, timeout='10')

            if item[1] == '404':
                return self.meta.append({'imdb': '0', 'tmdb': '0', 'tvdb': tvdb, 'lang': self.lang, 'user': self.user, 'item': {'code': '0'}})

            item = json.loads(item[0])

            tvshowtitle = item['name']
            tvshowtitle = tvshowtitle.encode('utf-8')
            if not tvshowtitle == '0': self.list[i].update({'tvshowtitle': tvshowtitle})

            year = item['premiered']
            year = re.findall('(\d{4})', year)[0]
            year = year.encode('utf-8')
            if not year == '0': self.list[i].update({'year': year})

            try: imdb = item['externals']['imdb']
            except: imdb = '0'
            if imdb == '' or imdb == None: imdb = '0'
            imdb = imdb.encode('utf-8')
            if self.list[i]['imdb'] == '0' and not imdb == '0': self.list[i].update({'imdb': imdb})

            try: studio = item['network']['name']
            except: studio = '0'
            if studio == '' or studio == None: studio = '0'
            studio = studio.encode('utf-8')
            if not studio == '0': self.list[i].update({'studio': studio})

            genre = item['genres']
            if genre == '' or genre == None or genre == []: genre = '0'
            genre = ' / '.join(genre)
            genre = genre.encode('utf-8')
            if not genre == '0': self.list[i].update({'genre': genre})

            try: duration = str(item['runtime'])
            except: duration = '0'
            if duration == '' or duration == None: duration = '0'
            try: duration = str(int(duration) * 60)
            except: pass
            duration = duration.encode('utf-8')
            if not duration == '0': self.list[i].update({'duration': duration})

            rating = str(item['rating']['average'])
            if rating == '' or rating == None: rating = '0'
            rating = rating.encode('utf-8')
            if not rating == '0': self.list[i].update({'rating': rating})

            plot = item['summary']
            if plot == '' or plot == None: plot = '0'
            plot = re.sub('\n|<.+?>|</.+?>|.+?#\d*:', '', plot)
            plot = plot.encode('utf-8')
            if not plot == '0': self.list[i].update({'plot': plot})

            self.meta.append({'imdb': imdb, 'tmdb': '0', 'tvdb': tvdb, 'lang': self.lang, 'user': self.user, 'item': {'tvshowtitle': tvshowtitle, 'year': year, 'code': imdb, 'imdb': imdb, 'tvdb': tvdb, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'plot': plot}})
        except:
            pass

    def addDirectory(self, items, queue=False, cache=True):
        if items == None or len(items) == 0: return

        sysaddon = sys.argv[0]
        addonPoster = addonBanner = control.addonInfo('icon')
        addonFanart = control.addonInfo('fanart')

        playlist = control.playlist
        if not queue == False: playlist.clear()

        try: devmode = True if 'testings.xml' in control.listDir(control.dataPath)[1] else False
        except: devmode = False

        try: 
            privmode = False
            pb_loc = str(control.setting('pb_private'))
            if len(pb_loc) == 8:
                privmode = True
        except: privmode = False

        mode = [i['content'] for i in items if 'content' in i]
        if 'movies' in mode: mode = 'movies'
        elif 'tvshows' in mode: mode = 'tvshows'
        elif 'seasons' in mode: mode = 'seasons'
        elif 'episodes' in mode: mode = 'episodes'
        elif 'videos' in mode: mode = 'videos'
        else: mode = 'addons'

        for i in items:
            try:
                
                try: name = control.lang(int(i['name'])).encode('utf-8')
                except: name = i['name']
                
                if name == '':
                    name = i['name']
                
                build = False
                if 'ADULT ZONE' in name:
                    if control.setting('adult') == 'true': build = True
                elif 'Parental Controls' in name:
                    if control.setting('adult') == 'true': build = True
                else: build = True
                
                if build:
                    url = '%s?action=%s' % (sysaddon, i['action'])
                    try: url += '&worker=%s' % i['worker']
                    except: pass
                    try: url += '&url=%s' % urllib.quote_plus(i['url'])
                    except: pass
                    try: url += '&content=%s' % urllib.quote_plus(i['content'])
                    except: pass
                    if i['action'] == 'plugin' and 'url' in i: url = i['url']

                    try: devurl = dict(urlparse.parse_qsl(urlparse.urlparse(url).query))['action']
                    except: devurl = None
                    if devurl == 'developer' and not devmode == True: raise Exception()

                    try: privurl = dict(urlparse.parse_qsl(urlparse.urlparse(url).query))['action']
                    except: privurl = None
                    if privurl == 'private' and not privmode == True: raise Exception()
                    
                    try: poster = i['poster3']
                    except: poster = '0'
                    
                    #if poster == '0':
                    #    try: poster = i['poster2']
                    #    except: poster = '0'
                    
                    if poster == '0':
                        try: poster = i['poster']
                        except: poster = '0'
                    

                    try: fanart = i['fanart2']
                    except: fanart = '0'
                    
                    if fanart == '0':
                        try: fanart = i['fanart'] if not 'fanart.tv' in i['fanart'] else '0'
                        except: fanart = '0'
                    
                    banner = i['banner'] if 'banner' in i else '0'

                    if poster == '0': poster = addonPoster
                    else: poster = re.sub('([a-zA-Z]+)\d+_([a-zA-Z]+)\d+,\d+,\d+,\d+', '\g<1>512_\g<2>0,0,0,512', poster)
                    if banner == '0' and poster == '0': banner = addonBanner
                    elif banner == '0': banner = poster
                    
                    content = i['content'] if 'content' in i else '0'

                    folder = i['folder'] if 'folder' in i else True

                    meta = dict((k,v) for k, v in i.iteritems() if not v == '0')
                    
                    if control.setting('metadata') == 'true':
                        try: name = meta['title'] + ' (%s)' % meta['year'] if not meta['year'] == '0' else meta['title']
                        except: pass    

                    cm = []

                    if content in ['movies', 'tvshows']:
                        meta.update({'trailer': '%s?action=trailer&name=%s' % (sysaddon, urllib.quote_plus(name))})
                        cm.append((control.lang(30707).encode('utf-8'), 'RunPlugin(%s?action=trailer&name=%s)' % (sysaddon, urllib.quote_plus(name))))

                    if content in ['movies', 'tvshows', 'seasons', 'episodes']:
                        cm.append((control.lang(30708).encode('utf-8'), 'XBMC.Action(Info)'))

                    if (folder == False and not '|regex=' in str(i.get('url'))) or (folder == True and content in ['tvshows', 'seasons']):
                        cm.append((control.lang(30723).encode('utf-8'), 'RunPlugin(%s?action=queueItem)' % sysaddon))

                    if content == 'movies':
                        try: dfile = '%s (%s)' % (i['title'], i['year'])
                        except: dfile = name
                        try: cm.append((control.lang(30722).encode('utf-8'), 'RunPlugin(%s?action=addDownload&name=%s&url=%s&image=%s)' % (sysaddon, urllib.quote_plus(dfile), urllib.quote_plus(i['url']), urllib.quote_plus(poster))))
                        except: pass
                    elif content == 'episodes':
                        try: dfile = '%s S%02dE%02d' % (i['tvshowtitle'], int(i['season']), int(i['episode']))
                        except: dfile = name
                        try: cm.append((control.lang(30722).encode('utf-8'), 'RunPlugin(%s?action=addDownload&name=%s&url=%s&image=%s)' % (sysaddon, urllib.quote_plus(dfile), urllib.quote_plus(i['url']), urllib.quote_plus(poster))))
                        except: pass
                    elif content == 'songs':
                        try: cm.append((control.lang(30722).encode('utf-8'), 'RunPlugin(%s?action=addDownload&name=%s&url=%s&image=%s)' % (sysaddon, urllib.quote_plus(name), urllib.quote_plus(i['url']), urllib.quote_plus(poster))))
                        except: pass

                    if mode == 'movies':
                        cm.append((control.lang(30711).encode('utf-8'), 'RunPlugin(%s?action=addView&content=movies)' % sysaddon))
                    elif mode == 'tvshows':
                        cm.append((control.lang(30712).encode('utf-8'), 'RunPlugin(%s?action=addView&content=tvshows)' % sysaddon))
                    elif mode == 'seasons':
                        cm.append((control.lang(30713).encode('utf-8'), 'RunPlugin(%s?action=addView&content=seasons)' % sysaddon))
                    elif mode == 'episodes':
                        cm.append((control.lang(30714).encode('utf-8'), 'RunPlugin(%s?action=addView&content=episodes)' % sysaddon))

                    if devmode == True:
                        try: cm.append(('Open in browser', 'RunPlugin(%s?action=browser&url=%s)' % (sysaddon, urllib.quote_plus(i['url']))))
                        except: pass

                    if privmode == True:
                        try: cm.append(('Open in browser', 'RunPlugin(%s?action=browser&url=%s)' % (sysaddon, urllib.quote_plus(i['url']))))
                        except: pass
                        
                    item = control.item(label=name, iconImage=poster, thumbnailImage=poster)

                    try: item.setArt({'poster': poster, 'tvshow.poster': poster, 'season.poster': poster, 'banner': banner, 'tvshow.banner': banner, 'season.banner': banner})
                    except: pass

                    if not fanart == '0':
                        item.setProperty('Fanart_Image', fanart)
                    elif not addonFanart == None:
                        item.setProperty('Fanart_Image', addonFanart)

                    if queue == False:
                        item.setInfo(type='Video', infoLabels = meta)
                        item.addContextMenuItems(cm)
                        control.addItem(handle=int(sys.argv[1]), url=url, listitem=item, isFolder=folder)
                    else:
                        item.setInfo(type='Video', infoLabels = meta)
                        playlist.add(url=url, listitem=item)
            except:
                pass

        if not queue == False:
            return control.player.play(playlist)

        try:
            i = items[0]
            if i['next'] == '': raise Exception()
            url = '%s?action=%s&url=%s' % (sysaddon, i['nextaction'], urllib.quote_plus(i['next']))
            item = control.item(label=control.lang(30500).encode('utf-8'))
            item.setArt({'addonPoster': addonPoster, 'thumb': addonPoster, 'poster': addonPoster, 'tvshow.poster': addonPoster, 'season.poster': addonPoster, 'banner': addonPoster, 'tvshow.banner': addonPoster, 'season.banner': addonPoster})
            item.setProperty('addonFanart_Image', addonFanart)
            control.addItem(handle=int(sys.argv[1]), url=url, listitem=item, isFolder=True)
        except:
            pass

        if not mode == None: control.content(int(sys.argv[1]), mode)
        if cache: control.directory(int(sys.argv[1]), cacheToDisc=True)
        else: control.directory(int(sys.argv[1]), cacheToDisc=False)
        if mode in ['movies', 'tvshows', 'seasons', 'episodes']:
            views.setView(mode, {'skin.estuary': 55})

class resolver:
    def browser(self, url):
        try:
            url = self.get(url)
            if url == False: return
            control.execute('RunPlugin(plugin://plugin.program.chrome.launcher/?url=%s&mode=showSite&stopPlayback=no)' % urllib.quote_plus(url))
        except:
            pass


    def link(self, url):
        try:
            url = self.get(url)
            if url == False: return

            control.execute('ActivateWindow(busydialog)')
            url = self.process(url)
            control.execute('Dialog.Close(busydialog)')

            if url == None: return control.infoDialog(control.lang(30705).encode('utf-8'))
            return url
        except:
            pass


    def get(self, url):
        try:
            items = re.compile('<sublink(?:\s+name=|)(?:\'|\"|)(.*?)(?:\'|\"|)>(.+?)</sublink>').findall(url)

            if len(items) == 0: return url
            if len(items) == 1: return items[0][1]

            dialog_list = []
            for i in items:
                if i[0] != '':
                    dialog_list += [(i[0], i[1])]
                elif '<preset>searchsd</preset>' in i[1]:  
                    dialog_list += [('SD (Lists provider, host & quality if available)', i[1])]
                elif '<preset>search</preset>' in i[1]:
                    dialog_list += [('AUTOPLAY (Best available stream - can be false at times)', i[1].replace('<preset>search</preset>','<preset>searchauto</preset>'))]
                    if not debrid.status() == False: 
                        dialog_list += [('Premium (Real Debrid, Premiumize, etc)', i[1].replace('<preset>search</preset>','<preset>searchrd</preset>'))]
                    dialog_list += [('HD (Lists provider, host & quality if available)', i[1])]

            select = control.selectDialog([i[0] for i in dialog_list], control.infoLabel('listitem.label'))

            if select == -1: return False
            else: return dialog_list[select][1]
        except:
            pass


    def f4m(self, url, name):
            try:
                if not any(i in url for i in ['.f4m', '.ts']): raise Exception()
                ext = url.split('?')[0].split('&')[0].split('|')[0].rsplit('.')[-1].replace('/', '').lower()
                if not ext: ext = url
                if not ext in ['f4m', 'ts']: raise Exception()

                params = urlparse.parse_qs(url)

                try: proxy = params['proxy'][0]
                except: proxy = None

                try: proxy_use_chunks = json.loads(params['proxy_for_chunks'][0])
                except: proxy_use_chunks = True

                try: maxbitrate = int(params['maxbitrate'][0])
                except: maxbitrate = 0

                try: simpleDownloader = json.loads(params['simpledownloader'][0])
                except: simpleDownloader = False

                try: auth_string = params['auth'][0]
                except: auth_string = ''

                try: streamtype = params['streamtype'][0]
                except: streamtype = 'TSDOWNLOADER' if ext == 'ts' else 'HLS'

                try: swf = params['swf'][0]
                except: swf = None

                from F4mProxy import f4mProxyHelper
                return f4mProxyHelper().playF4mLink(url, name, proxy, proxy_use_chunks, maxbitrate, simpleDownloader, auth_string, streamtype, False, swf)
            except:
                pass


    def process(self, url, direct=True):
        try:
            if not any(i in url for i in ['.jpg', '.png', '.gif']): raise Exception()
            ext = url.split('?')[0].split('&')[0].split('|')[0].rsplit('.')[-1].replace('/', '').lower()
            if not ext in ['jpg', 'png', 'gif']: raise Exception()
            try:
                i = os.path.join(control.dataPath,'img')
                control.deleteFile(i)
                f = control.openFile(i, 'w')
                f.write(client.request(url))
                f.close()
                control.execute('ShowPicture("%s")' % i)
                return False
            except:
                return
        except:
            pass

        try:
            r, x = re.findall('(.+?)\|regex=(.+?)$', url)[0]
            x = regex.fetch(x)
            r += urllib.unquote_plus(x)
            if not '</regex>' in r: raise Exception()
            u = regex.resolve(r)
            if not u == None: url = u
        except:
            pass

        try:
            if not url.startswith('rtmp'): raise Exception()
            if len(re.compile('\s*timeout=(\d*)').findall(url)) == 0: url += ' timeout=10'
            return url
        except:
            pass

        try:
            if not any(i in url for i in ['.m3u8', '.f4m', '.ts']): raise Exception()
            ext = url.split('?')[0].split('&')[0].split('|')[0].rsplit('.')[-1].replace('/', '').lower()
            if not ext in ['m3u8', 'f4m', 'ts']: raise Exception()
            return url
        except:
            pass

        try:
        
            preset = re.findall('<preset>(.+?)</preset>', url)[0]

            if not 'search' in preset: raise Exception()

            try: title, year, imdb = re.findall('<title>(.+?)</title>', url)[0], re.findall('<year>(.+?)</year>', url)[0], re.findall('<imdb>(.+?)</imdb>', url)[0]
            except: title, year, imdb = re.findall('<tvshowtitle>(.+?)</tvshowtitle>', url)[0], re.findall('<year>(.+?)</year>', url)[0], re.findall('<imdb>(.+?)</imdb>', url)[0]

            try: tvdb, tvshowtitle, premiered, season, episode = re.findall('<tvdb>(.+?)</tvdb>', url)[0], re.findall('<tvshowtitle>(.+?)</tvshowtitle>', url)[0], re.findall('<premiered>(.+?)</premiered>', url)[0], re.findall('<season>(.+?)</season>', url)[0], re.findall('<episode>(.+?)</episode>', url)[0]
            except: tvdb = tvshowtitle = premiered = season = episode = None

            direct = False

            if preset == 'search': quality = 'HD'
            elif preset == 'searchrd': quality = 'RD'
            elif preset == 'searchauto': quality = 'AUTO'
            else: quality = 'SD'

            from resources.lib.modules import sources

            u = sources.sources().getSources(title, year, imdb, tvdb, season, episode, tvshowtitle, premiered, quality)

            if not u == None: return u
        except:
            pass

        try:
            from resources.lib.modules import sources

            u = sources.sources().getURISource(url)

            if not u == False: direct = False
            if u == None or u == False: raise Exception()

            return u
        except:
            pass

        try:
            if not '.google.com' in url: raise Exception()
            from resources.lib.modules import directstream
            u = directstream.google(url)[0]['url']
            return u
        except:
            pass

        try:
            if not 'filmon.com/' in url: raise Exception()
            from resources.lib.modules import filmon
            u = filmon.resolve(url)
            return u
        except:
            pass

        try:
            import resolveurl

            hmf = resolveurl.HostedMediaFile(url=url)

            if hmf.valid_url() == False: raise Exception()

            direct = False ; u = hmf.resolve()

            if not u == False: return u
        except:
            pass

        if direct == True: return url


class player(xbmc.Player):
    def __init__ (self):
        xbmc.Player.__init__(self)


    def play(self, url, content=None):
        try:
            base = url

            url = resolver().get(url)

            if url == False: return

            control.execute('ActivateWindow(busydialog)')
            url = resolver().process(url)
            control.execute('Dialog.Close(busydialog)')

            if url == None: return control.infoDialog(control.lang(30705).encode('utf-8'))
            if url == False: return

            meta = {}
            for i in ['title', 'originaltitle', 'tvshowtitle', 'year', 'season', 'episode', 'genre', 'rating', 'votes', 'director', 'writer', 'plot', 'tagline']:
                try: meta[i] = control.infoLabel('listitem.%s' % i)
                except: pass
            meta = dict((k,v) for k, v in meta.iteritems() if not v == '')
            if not 'title' in meta: meta['title'] = control.infoLabel('listitem.label')
            icon = control.infoLabel('listitem.icon')


            self.name = meta['title'] ; self.year = meta['year'] if 'year' in meta else '0'

            self.getbookmark = True if (content == 'movies' or content == 'episodes') else False

            self.offset = bookmarks().get(self.name, self.year)

            f4m = resolver().f4m(url, self.name)
            if not f4m == None: return


            item = control.item(path=url, iconImage=icon, thumbnailImage=icon)
            try: item.setArt({'icon': icon})
            except: pass
            item.setInfo(type='Video', infoLabels = meta)
            control.player.play(url, item)
            control.resolve(int(sys.argv[1]), True, item)

            self.totalTime = 0 ; self.currentTime = 0

            for i in range(0, 240):
                if self.isPlayingVideo(): break
                control.sleep(1000)
            while self.isPlayingVideo():
                try:
                    self.totalTime = self.getTotalTime()
                    self.currentTime = self.getTime()
                except:
                    pass
                control.sleep(2000)
            control.sleep(5000)
        except:
            pass


    def onPlayBackStarted(self):
        control.execute('Dialog.Close(all,true)')
        if self.getbookmark == True and not self.offset == '0':
            self.seekTime(float(self.offset))


    def onPlayBackStopped(self):
        if self.getbookmark == True:
            bookmarks().reset(self.currentTime, self.totalTime, self.name, self.year)


    def onPlayBackEnded(self):
        self.onPlayBackStopped()



class bookmarks:
    def get(self, name, year='0'):
        try:
            offset = '0'

            #if not control.setting('bookmarks') == 'true': raise Exception()

            idFile = hashlib.md5()
            for i in name: idFile.update(str(i))
            for i in year: idFile.update(str(i))
            idFile = str(idFile.hexdigest())

            dbcon = database.connect(control.bookmarksFile)
            dbcur = dbcon.cursor()
            dbcur.execute("SELECT * FROM bookmark WHERE idFile = '%s'" % idFile)
            match = dbcur.fetchone()
            self.offset = str(match[1])
            dbcon.commit()

            if self.offset == '0': raise Exception()

            minutes, seconds = divmod(float(self.offset), 60) ; hours, minutes = divmod(minutes, 60)
            label = '%02d:%02d:%02d' % (hours, minutes, seconds)
            label = (control.lang(32502) % label).encode('utf-8')

            try: yes = control.dialog.contextmenu([label, control.lang(32501).encode('utf-8'), ])
            except: yes = control.yesnoDialog(label, '', '', str(name), control.lang(32503).encode('utf-8'), control.lang(32501).encode('utf-8'))

            if yes: self.offset = '0'

            return self.offset
        except:
            return offset


    def reset(self, currentTime, totalTime, name, year='0'):
        try:
            #if not control.setting('bookmarks') == 'true': raise Exception()

            timeInSeconds = str(currentTime)
            ok = int(currentTime) > 180 and (currentTime / totalTime) <= .92

            idFile = hashlib.md5()
            for i in name: idFile.update(str(i))
            for i in year: idFile.update(str(i))
            idFile = str(idFile.hexdigest())

            control.makeFile(control.dataPath)
            dbcon = database.connect(control.bookmarksFile)
            dbcur = dbcon.cursor()
            dbcur.execute("CREATE TABLE IF NOT EXISTS bookmark (""idFile TEXT, ""timeInSeconds TEXT, ""UNIQUE(idFile)"");")
            dbcur.execute("DELETE FROM bookmark WHERE idFile = '%s'" % idFile)
            if ok: dbcur.execute("INSERT INTO bookmark Values (?, ?)", (idFile, timeInSeconds))
            dbcon.commit()
        except:
            pass