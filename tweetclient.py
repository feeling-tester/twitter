# coding:utf-8
from __future__ import print_function
import oauth2 
import sys
import sqlite3
import twitter
import urllib
import webbrowser as web
import ast
from contextlib import closing
from contextlib import contextmanager
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty
from kivy.config import Config
import configparser

Config.set('input', 'mouse', 'mouse,disable_multitouch') 
config = configparser.ConfigParser()
config.read('setting.ini')

def load_app_keys():
    return config['APPKEY']['CONSUMER_KEY'], config['APPKEY']['CONSUMER_SECRET']

def load_access_tokens():
    return config['ACCOUNT']['SELECTED_ACCESS_TOKEN_KEY'], config['ACCOUNT']['SELECTED_ACCESS_TOKEN_SECRET']
    
class SelectAccountScreen(BoxLayout, Screen):
    dbname = 'Account.db'
    infomation = ObjectProperty(None)
    account = ObjectProperty(None)
    ACS = ''

    def get_sql_data(self, search_sql, account_id):
        with closing(sqlite3.connect(dbname)) as conn:
            c = conn.cursor()
            search_sql = search_sql + '"' + account_id + '"';
            cur = c.execute(search_sql)
            ret = str(cur.fetchall())
            a = ret.split("'")
        conn.close()
        return a[1]

    def get_access_token_key(self, account_id):
        search_sql = 'select oauth_token from users where screen_name='
        return self.get_sql_data(search_sql, account_id)
    
    def get_access_token_secret(self, account_id):
        search_sql = 'select oauth_token_secret from users where screen_name='
        return self.get_sql_data(search_sql, account_id)

    def set_account(self):
        try:
            print("Enter your Account ID : ", end="")
            print(self.account.text)
            account_id = self.account.text
            #print(account_id)
            account_hit = False
            access_token_key = ''
            access_token_secret = ''
            #print("AAAA")

            with closing(sqlite3.connect(dbname)) as conn:
                c = conn.cursor()
                search_sql = 'select * from users where screen_name='
                search_sql = search_sql + '"' + account_id + '"';
                cur = c.execute(search_sql)
                # if len(cur.fetchall()):
                account_hit = True
                access_token_key = self.get_access_token_key(account_id)
                access_token_secret = self.get_access_token_secret(account_id)
                # else:
                #     account_hit = False
            conn.close()

            # if (account_hit == False):
            # print("Sorry, but the account is not registered")
            #     sys.exit()
            #print("AAAA")

            section1 = 'ACCOUNT'
            config.set(section1, 'SELECTED_ACCOUNT_ID', account_id)
            config.set(section1, 'SELECTED_ACCESS_TOKEN_KEY', access_token_key)
            config.set(section1, 'SELECTED_ACCESS_TOKEN_SECRET', access_token_secret)
            with open('setting.ini', 'w') as file:
                config.write(file)
                
            #print("AAAA")
            CK, CS = load_app_keys()
            ATK, ATS = load_access_tokens()
            #print(CK)
            api = twitter.Api(consumer_key=CK,
                              consumer_secret=CS,
                              access_token_key=ATK,
                              access_token_secret=ATS
            )

            #api.PostUpdate("set Account")
            self.infomation.text = account_id + " is selected."
        except IndexError:
            print("IndexError")
            self.infomation.text = "The account is not registered."
        except KeyError:
            print("KeyError")
        except ValueError:
            print("ValueError")
        except NameError:
            print("NameError")

class RegistAccountScreen(BoxLayout, Screen):
    oauth_data = ''
    number = ObjectProperty(None)
    #message = ObjectProperty(None)
    def get_request_token(self):
        CK, CS = load_app_keys()
        consumer = oauth2.Consumer(key=CK, secret=CS)
        client = oauth2.Client(consumer)
        response, content = client.request("https://api.twitter.com/oauth/request_token", "GET")
        content = (content.decode())
        oauth_data = dict(urllib.parse.parse_qsl(content))
        # ex. oauth_data =
        # {'oauth_token_secret': 'Number and Alphabet',
        #  'oauth_token': 'Number and Alphabet',
        #  'oauth_callback_confirmed': 'true or false'}
        return oauth_data
    
    def get_access_token(self, oauth_token, oauth_verifier):
        CK, CS = load_app_keys()
        consumer = oauth2.Consumer(key=CK, secret=CS)
        token = oauth2.Token(oauth_token, oauth_verifier)
        client = oauth2.Client(consumer, token)
        response, content = client.request("https://api.twitter.com/oauth/access_token", "POST", body="oauth_verifier={0}".format(oauth_verifier))
        content = (content.decode())
        oauth_data = dict(urllib.parse.parse_qsl(content))
        # ex. oauth_data =
        # {'oauth_token_secret': 'Number and Alphabet',
        #  'user_id': 'Number',
        #  'x_auth_expires': 'Number',
        #  'oauth_token': 'Number-Number and Alphabet',
        #  'screen_name': 'Account ID'}
        return oauth_data
    
    def setup_account(self):
        oauth = self.get_request_token()
        #oauth_data = ast.literal_eval(oauth_data)
        # self.message.text="a"
        # print(self.message.text)
        #print(oauth)
        url = "https://api.twitter.com/oauth/authorize?oauth_token=" + oauth['oauth_token']
        browser = web.get('"/usr/bin/chromium-browser" %s')
        browser.open(url)
        global oauth_data
        oauth_data = oauth
    
    def enter_pin(self):
        # PIN input
        try:
            global oauth_data
            print("Enter your PIN code : ")
            print(self.number.text)
            #oauth_verifier = input()
            oauth_verifier = self.number.text
            
            # parameter settings
            oauth_token = oauth_data['oauth_token']
            oauth_token_secret =  oauth_data['oauth_token_secret']    
            oauth_data = self.get_access_token(oauth_token, oauth_verifier)

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
                    msg = "The account is already registered."
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
                    msg = "Account registration is completed."
                conn.close()
            self.infomation.text = msg

        except KeyError:
            print("Error")
            self.infomation.text = "PIN code may be wrong"

        except NameError:
            print("Error2")
            self.infomation.text = "Verify account on the browser"
            
class TimelineScreen(BoxLayout, Screen):
    #global infomation_message
    infomation = ObjectProperty(None)
    tweet_input_form = ObjectProperty(None)
    tweet_view = ObjectProperty(None)
    
    def post_tweet(self):        
        try:
            CK, CS = load_app_keys()
            ATK, ATS = load_access_tokens()

            tweet = self.tweet_input_form.text
            api = twitter.Api(consumer_key=CK,
                              consumer_secret=CS,
                              access_token_key=ATK,
                              access_token_secret=ATS
            )
        
            api.PostUpdate(tweet)
            self.infomation.text = tweet + " is tweeted."
        except twitter.error.TwitterError:
            print("Something Twitter Error")

        except NameError:
            print("Error2")
            self.infomation.text = "Something error occurred"
            
class ClientApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(RegistAccountScreen(name='register'))
        sm.add_widget(SelectAccountScreen(name='select'))
        sm.add_widget(TimelineScreen(name='timeline'))
        return sm
        #return TimelineScreen()

    def on_enter(self, ti):
        print("on_enter[%s]" % (ti.text))

if __name__ == "__main__":
    dbname = 'Account.db'
    ClientApp().run()

    ######
    sys.exit()
    ######

