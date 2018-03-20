# coding:utf-8
from __future__ import print_function
import sys, config
sys.path.append('/usr/local/lib/python2.7/dist-packages/python_twitter-3.4.1-py2.7.egg')

import sqlite3
import twitter
from contextlib import closing

def get_sql_data(search_sql):
    search_sql = search_sql + '"' + account_id + '"';
    cur = c.execute(search_sql)
    ret = str(cur.fetchall())
    a = ret.split("'")
    return a[1]
    
def get_access_token_key():
    search_sql = 'select oauth_token from users where screen_name='
    return get_sql_data(search_sql)

def get_access_token_secret():
    search_sql = 'select oauth_token_secret from users where screen_name='
    return get_sql_data(search_sql)
    
if __name__ == "__main__":
    dbname = 'Account.db'
    print("Enter your Account ID : ", end="")
    account_id = raw_input()
    account_hit = False
    access_token_key = ''
    access_token_secret = ''
    
    with closing(sqlite3.connect(dbname)) as conn:
        c = conn.cursor()
        search_sql = 'select * from users where screen_name='
        search_sql = search_sql + '"' + account_id + '"';
        cur = c.execute(search_sql)
        if len(cur.fetchall()):
            account_hit = True
            access_token_key = get_access_token_key()
            access_token_secret = get_access_token_secret()
        else:
            account_hit = False
        conn.close()

    if (account_hit == False):
        print("Sorry, but the account is not registered")
        sys.exit()
    
    api = twitter.Api(consumer_key=config.CONSUMER_KEY,
                      consumer_secret=config.CONSUMER_SECRET,
                      access_token_key=access_token_key,
                      access_token_secret=access_token_secret
    )
    print("tweet : ", end="")
    tweet = raw_input()
    api.PostUpdate(tweet)
