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
import simplejson as json
import datetime
import inspect
from google.appengine.ext import db
from google.appengine.api import users

class tweet_store(db.Model):
    tweet = db.StringProperty(multiline=True)
    author = db.StringProperty(multiline=True)
    time = db.StringProperty(multiline=True)
    n = db.StringProperty()

def tweet_key(tweet_name=None):
    return db.Key.from_path('tweet', tweet_name or 'default_tweet')
    
class tag_store(db.Model):
    tag = db.StringProperty(multiline=True)

def tag_key(tag_name=None):
    return db.Key.from_path('tag', tag_name or 'default_tag')
    
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
            if(quote==""):
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
            time = x['created_at']
            values ={
              'tweet': tweet,
              'author': author,
              'id': count,
              'time': time
            }
            path = os.path.join(os.path.dirname(__file__), 'tweet.html')
            # tweet_db = tweet_store(parent=tweet_key(tweet))
            # tweet_db.tweet = tweet
            # tweet_db.author = author
            # tweet_db.time = time
            # tweet_db.put()
            self.response.out.write(template.render(path, values))
        
        values = {
            'count': count
        }
        path = os.path.join(os.path.dirname(__file__), 'footer.html')
        self.response.out.write(template.render(path, values))

class Showdb(webapp.RequestHandler):
    def get(self):
        values = []
        path = os.path.join(os.path.dirname(__file__), 'header.html')
        self.response.out.write(template.render(path, values))

        tweets = db.GqlQuery("SELECT * from tweet_store")
        count = 0
        previous = ""
        for tweet in tweets:
            count +=1
            values ={
               'tweet': tweet.tweet,
               'author': tweet.author,
               'id': count,
               'time': tweet.time,
               'n':tweet.n
            }
            if tweet.n == previous:
                continue
            else:
                previous = tweet.n
            path = os.path.join(os.path.dirname(__file__), 'tweet.html')
            self.response.out.write(template.render(path, values))
        
        path = os.path.join(os.path.dirname(__file__), 'footer.html')
        self.response.out.write(template.render(path, values))

class Cron(webapp.RequestHandler):
    def get(self):
        values = []
        path = os.path.join(os.path.dirname(__file__), 'cron.html')
        self.response.out.write(template.render(path, values))
        path = os.path.join(os.path.dirname(__file__), 'footer.html')
        self.response.out.write(template.render(path, values))
        
class SaveTags(webapp.RequestHandler):
    def post(self):
        tag = self.request.get('tag')
        tag_db = tag_store(parent=tag_key(tag))
        tag_db.tag = tag
        tag_db.put()
        tags = db.GqlQuery("SELECT * from tag_store")
        self.response.out.write("Tags stored: <br/>")
        for tag in tags:
            self.response.out.write(tag.tag + "<br/>")
        
class GetTags(webapp.RequestHandler):
    def get(self):
        tags = db.GqlQuery("SELECT * from tag_store")
        for tag in tags:
            self.response.out.write(tag.tag + "<br/>")

class BackgroundSearch(webapp.RequestHandler):
    def get(self):
        tweets = db.GqlQuery("SELECT * from tweet_store")
        since_id = ""
        for t in tweets:
            since_id = t.n

        tags = db.GqlQuery("SELECT * from tag_store")
        query = ""
        for tag in tags:
            query = tag.tag
            url = 'http://search.twitter.com/search.json?q=' + query + '&rpp=100&since_id=' + since_id
            content = urlopen(url).read()
            content_json = json.loads(content)['results']
            count = 0          
            for x in content_json:
                count +=1
                author = x['from_user']
                tweet = x['text']
                time = x['created_at']
                n = str(x['id'])
                values ={
                    'tweet': tweet,
                    'author': author,
                    'id': count,
                    'time': time,
                    'n': n
                    }
                tweet_db = tweet_store(parent=tweet_key(tweet))
                tweet_db.tweet = tweet
                tweet_db.author = author
                tweet_db.time = time
                tweet_db.n = n
                tweet_db.put()

class DeleteTweet(webapp.RequestHandler):
    def post(self):
        n = self.request.get('n')
        tweets = db.GqlQuery("SELECT * from tweet_store WHERE n=:1", n)
        for t in tweets:
            t.delete()

class EmptyTable(webapp.RequestHandler):
    def get(self):
        tweets = db.GqlQuery("SELECT * from tweet_store")
        for tweet in tweets:
            tweet.delete()
        self.response.out.write("Emptied")
    
class MainPage(webapp.RequestHandler):
    def get(self):
       values = []
       path = os.path.join(os.path.dirname(__file__), 'twitter.html')
       self.response.out.write(template.render(path, values))


application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                     ('/tumblr', tumblr),
                                     ('/hashtag', hashtag),
                                     ('/saved', Showdb),
                                     ('/tags', Cron),
                                     ('/savetags', SaveTags),
                                     ('/gettags', GetTags),
                                     ('/background', BackgroundSearch),
                                     ('/deletetweet', DeleteTweet),
                                     ('/empty', EmptyTable)],
                                     debug=True)

def main():
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()