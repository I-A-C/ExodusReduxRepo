# -*- coding: utf-8 -*-

import re
import urllib
import urlparse
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import proxy


class source:
    def __init__(self):
        self.name = 'Movie Trailers'       
        self.priority = 1
        self.language = ['en']
        self.domains = ['hdm.to']
        self.base_link = 'https://hdm.to'

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = cleantitle.geturl(title)
            return url
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []
            url = '%s/%s/' % (self.base_link,url)
            r = client.request(url)
            try:
                match = re.compile('<iframe.+?src="(.+?)"').findall(r)
                for url in match:
#                    if 'openload' in url:
#                        Provider = 'Openload.co'
#                        Direct = False
#                        Quality = 'HD'
                    if 'youtube' in url:
                        Provider = 'DirectLink'
                        Direct = True
                        Quality = 'HD'
                        sources.append({'source': Provider,'quality': Quality,'language': 'en','url': url,'direct': False,'debridonly': False}) 
#                    sources.append({'source': Provider,'quality': Quality,'language': 'en','url': url,'direct': False,'debridonly': False}) 
                return sources

            except:
                return
        except Exception:
            return
        # return sources

    def resolve(self, url):
         return url
