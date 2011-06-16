#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
import os
from google.appengine.ext.webapp import template
from urllib import urlopen
import httplib, urllib, urllib2
import json

class tumblr(webapp.RequestHandler):
    def post(self):
        url = 'http://www.tumblr.com/api/write'
        email = self.request.get('email')
        password = self.request.get('password')
        post_type = "quote"
        group = self.request.get('group')
        count = self.request.get('count')
        i=0

        while(i!=int(count)):
            quote = self.request.get('quote' + str(i+1))
            s = self.request.get('source' + str(i+1))
            if(s==""):
                self.response.out.write(s)
            else:
                source = '<a href = "http://twitter.com/' + s + '">' + s + "</a>"
                p = {'email': email, 'password': password, 'type': post_type, 'group': group, 'quote':quote, 'source':source, 'state':'queue' }
                str_p = {}
                for k, v in p.iteritems():
                    str_p[k] = unicode(v).encode('utf-8')
                params = urllib.urlencode(str_p)
                req = urllib2.Request(url, params)
                urllib2.urlopen(req)
            i+=1


class hashtag(webapp.RequestHandler):
    def post(self):
        tweet = []
        author = []
        values = []
        q = self.request.get('query')
        n = self.request.get('number')
        url = 'http://search.twitter.com/search.json?q=' + q + '&rpp=' + n
        content = urlopen(url).read()
        content_json = json.loads(content)['results']
        count = 0

        path = os.path.join(os.path.dirname(__file__), 'header.html')
        self.response.out.write(template.render(path, values))

        for x in content_json:
            count +=1
            author = x['from_user']
            tweet = x['text']
            values ={
              'tweet': tweet,
              'author': author,
              'id': count,
            }
            path = os.path.join(os.path.dirname(__file__), 'tweet.html')
            self.response.out.write(template.render(path, values))

        path = os.path.join(os.path.dirname(__file__), 'footer.html')
        self.response.out.write(template.render(path, values))


class MainPage(webapp.RequestHandler):
    def get(self):
       values = []
       path = os.path.join(os.path.dirname(__file__), 'twitter.html')
       self.response.out.write(template.render(path, values))


application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                     ('/tumblr', tumblr),
                                     ('/hashtag', hashtag)],
                                     debug=True)

def main():
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
