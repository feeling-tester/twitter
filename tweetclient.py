# coding:utf-8
from __future__ import print_function
import oauth2 
import sys, config
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


CK = ''
CS = ''
ATK = ''
ACS = ''

def get_sql_data(search_sql, account_id):
    with closing(sqlite3.connect(dbname)) as conn:
        c = conn.cursor()
        search_sql = search_sql + '"' + account_id + '"';
        cur = c.execute(search_sql)
        ret = str(cur.fetchall())
        a = ret.split("'")
        conn.close()
    return a[1]
    
def get_access_token_key(account_id):
    search_sql = 'select oauth_token from users where screen_name='
    return get_sql_data(search_sql, account_id)

def get_access_token_secret(account_id):
    search_sql = 'select oauth_token_secret from users where screen_name='
    return get_sql_data(search_sql, account_id)

class SelectAccountScreen(BoxLayout, Screen):
    dbname = 'Account.db'
    infomation = ObjectProperty(None)
    account = ObjectProperty(None)

    def set_account(self):
        try:
            print("Enter your Account ID : ", end="")
            print(self.account.text)
            account_id = self.account.text
            print(account_id)
            account_hit = False
            access_token_key = ''
            access_token_secret = ''
            
            with closing(sqlite3.connect(dbname)) as conn:
                c = conn.cursor()
                search_sql = 'select * from users where screen_name='
                search_sql = search_sql + '"' + account_id + '"';
                cur = c.execute(search_sql)
                # if len(cur.fetchall()):
                account_hit = True
                access_token_key = get_access_token_key(account_id)
                access_token_secret = get_access_token_secret(account_id)
                # else:
                #     account_hit = False
            conn.close()

            # if (account_hit == False):
            # print("Sorry, but the account is not registered")
            #     sys.exit()
                
            api = twitter.Api(consumer_key=config.CONSUMER_KEY,
                              consumer_secret=config.CONSUMER_SECRET,
                              access_token_key=access_token_key,
                              access_token_secret=access_token_secret
            )
            global CK, CS, ATK, ATS
            CK = config.CONSUMER_KEY
            CS = config.CONSUMER_SECRET
            ATK = access_token_key
            ATS = access_token_secret
            #api.PostUpdate("set Account")

        except IndexError:
            print("IndexError")    
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
        consumer = oauth2.Consumer(key=config.CONSUMER_KEY, secret=config.CONSUMER_SECRET)
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
        consumer = oauth2.Consumer(key=config.CONSUMER_KEY, secret=config.CONSUMER_SECRET)
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
            print(type(msg))
            self.infomation.text = msg

        except KeyError:
            print("Error")
            self.infomation.text = "PIN code may be wrong"

        except NameError:
            print("Error2")
            self.infomation.text = "Something error occurred"
            
class TimelineScreen(BoxLayout, Screen):
    #global infomation_message
    infomation = ObjectProperty(None)
    tweet_input_form = ObjectProperty(None)
    tweet_view = ObjectProperty(None)
    
    def post_tweet(self):
        global CK, CS, ATK, ATS
        try: 
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

