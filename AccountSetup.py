# coding:utf-8
from __future__ import print_function
import sys, os
sys.path.append('/usr/local/lib/python2.7/dist-packages/python_twitter-3.4.1-py2.7.egg')

import twitter
import config
import oauth2 
import urlparse
import webbrowser as web
import json
import sqlite3
from contextlib import closing

def get_request_token():
    consumer = oauth2.Consumer(key=config.CONSUMER_KEY, secret=config.CONSUMER_SECRET)
    client = oauth2.Client(consumer)
    response, content = client.request("https://api.twitter.com/oauth/request_token", "GET")
    oauth_data = dict(urlparse.parse_qsl(content))
    # ex. oauth_data =
    # {'oauth_token_secret': 'Number and Alphabet',
    #  'oauth_token': 'Number and Alphabet',
    #  'oauth_callback_confirmed': 'true or false'}
    return oauth_data

def get_access_token(oauth_token, oauth_verifier):
    consumer = oauth2.Consumer(key=config.CONSUMER_KEY, secret=config.CONSUMER_SECRET)
    token = oauth2.Token(oauth_token, oauth_verifier)
    client = oauth2.Client(consumer, token)
    response, content = client.request("https://api.twitter.com/oauth/access_token", "POST", body="oauth_verifier={0}".format(oauth_verifier))
    oauth_data = dict(urlparse.parse_qsl(content))
    # ex. oauth_data =
    # {'oauth_token_secret': 'Number and Alphabet',
    #  'user_id': 'Number',
    #  'x_auth_expires': 'Number',
    #  'oauth_token': 'Number-Number and Alphabet',
    #  'screen_name': 'Account ID'}
    return oauth_data

if __name__ == "__main__":
    oauth_data = get_request_token()
    url = "https://api.twitter.com/oauth/authorize?oauth_token=" + oauth_data['oauth_token']
    browser = web.get('"/usr/bin/chromium-browser" %s')
    browser.open(url)

    # PIN input
    print("Enter your PIN code : ", end="")
    oauth_verifier = raw_input()

    # parameter settings
    oauth_token = oauth_data['oauth_token']
    oauth_token_secret =  oauth_data['oauth_token_secret']    
    oauth_data = get_access_token(oauth_token, oauth_verifier)
    
    # register account to DB 
    dbname = 'Account.db'
    with closing(sqlite3.connect(dbname)) as conn:
        c = conn.cursor()
        search_sql = 'select * from users where screen_name='
        search_sql = search_sql + '"' + oauth_data['screen_name'] + '"';
        #print(search_sql)
        cur = c.execute(search_sql)
        if len(cur.fetchall()):
            print("The account is already registered.")
        else:
            insert_sql = 'insert into users (oauth_token_secret, user_id, x_auth_expires, oauth_token, screen_name) values (?,?,?,?,?)'
            account_data = (oauth_data['oauth_token_secret'],
                            oauth_data['user_id'],
                            oauth_data['x_auth_expires'],
                            oauth_data['oauth_token'],
                            oauth_data['screen_name']
            )
            c.execute(insert_sql, account_data)
            conn.commit()
            print("Account registration is completed.")
        conn.close()
   
    # api = twitter.Api(consumer_key=config.CONSUMER_KEY,
    #                   consumer_secret=config.CONSUMER_SECRET,
    #                   access_token_key=oauth_data['oauth_token'],
    #                   access_token_secret=oauth_data['oauth_token_secret']
    # )

    
    #api.PostUpdate("")


