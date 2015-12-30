from flask import Flask
from telegram import Bot
import requests

from google.appengine.api import urlfetch
urlfetch.set_default_fetch_deadline(60)

from google.appengine.ext import ndb

class NbdGoulashBotStore(ndb.Model):
    last_update_id = ndb.IntegerProperty()
    users = ndb.JsonProperty()

    def read_last_update_id(self):
        return self.last_update_id

    def save_last_update_id(self, update_id):
        self.last_update_id = update_id
        self.put()

    def read_users(self):
        return self.users

    def add_user(self, user_id, chat_id):
        self.users[user_id] = chat_id
        self.put()

    @classmethod
    def get(cls):
        single = cls.query().get()
        if single:
            return single
        else:
            return NbdGoulashBotStore(last_update_id = 0, users = {})

class NbdGoulashFound(ndb.Model):
    found = ndb.BooleanProperty()

    def read_found(self):
        return self.found

    def save_found(self, found):
        self.found = found
        self.put()

    @classmethod
    def get(cls):
        single = cls.query().get()
        if single:
            return single
        else:
            return NbdGoulashFound(found = False)


class GoulashBot:

    def __init__(self, token):
        self.store = NbdGoulashBotStore.get()
        self.last_update_id = 0
        self.users = {}
        self.bot = Bot(token)
        self.goulash_found = NbdGoulashFound.get()
        for update in self.bot.getUpdates():
            self.process_message(update)

    def load_data(self):
        self.last_update_id = self.store.read_last_update_id()
        self.users = self.store.read_users()
        
    def add_user(self, user, chat_id):
        if user not in self.users.keys():
            self.store.add_user(user, chat_id)
            self.users[user] = chat_id
            self.bot.sendMessage(chat_id=chat_id, text=("Registrado"))
        else:
            self.bot.sendMessage(chat_id=chat_id, text=("Ya estabas registrado"))

    def process_message(self, update):
        chat_id = update.message.chat_id
        message = update.message.text
        username = str(update.message.from_user.id)

        if (message):
            self.add_user(username, chat_id)
        self.last_update_id = update.update_id + 1
        self.store.save_last_update_id(self.last_update_id)

    # Correr periodicamente
    def check_for_messages(self):
        for update in self.bot.getUpdates(offset=self.last_update_id):
            self.process_message(update)

    def goulash(self):
        response = requests.get('http://latropilla.platosdeldia.com/modules.php?name=PDD&func=nick&nick=latropilla')
        return (response.text.find('ulash') != -1) or (response.text.find('spaetzle') != -1) or (response.text.find('speciale') != -1)

    # Correr una vez al dia
    def reset_goulash_flag(self):
        self.goulash_found.save_found(False)

    def goulash_alert(self):
        for user in self.users.keys():
            self.bot.sendMessage(chat_id=self.users[user], text=("HAY GOULASH!!!!"))

    # Correr periodicamente
    def check_for_goulash(self):
        if not self.goulash_found.read_found():
            self.goulash_found.save_found(self.goulash())
            if self.goulash_found.read_found():
                self.goulash_alert()



app = Flask(__name__)
app.config['DEBUG'] = True

goulash_bot = GoulashBot('***REMOVED***')
goulash_bot.load_data()

@app.route('/cron/check_for_messages')
def check_for_messages():
    goulash_bot.check_for_messages()
    return str(goulash_bot.users)

@app.route('/cron/check_for_goulash')
def check_for_goulash():
    goulash_bot.check_for_goulash()
    return "Goulash found" if goulash_bot.goulash_found else "Goulash not found"

@app.route('/cron/reset_goulash_flag')
def reset_goulash_flag():
    goulash_bot.reset_goulash_flag()
    return 'Reseted.'

@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, nothing at this URL.', 404
