# -*- coding: utf-8 -*-

from flask import Flask
from telegram import Bot
import requests
import re

from google.appengine.api import urlfetch

urlfetch.set_default_fetch_deadline(60)

from google.appengine.ext import ndb

class NbdConfiguration(ndb.Model):
    temperature_apikey = ndb.StringProperty()
    telegram_apikey = ndb.StringProperty()
    ifttt_key = ndb.StringProperty()
    
    @classmethod
    def get(cls):
        single = cls.query().get()
        if single:
            return single
        else:
            None

        

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

    def remove_user(self, user_id, chat_id):
        del self.users[user_id]
        self.put()

    @classmethod
    def get(cls):
        single = cls.query().get()
        if single:
            return single
        else:
            return NbdGoulashBotStore(last_update_id=0, users={})


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
            return NbdGoulashFound(found=False)


class GoulashBot:
    def __init__(self):
        self.configuration = NbdConfiguration.get()
        self.store = NbdGoulashBotStore.get()
        self.last_update_id = 0
        self.users = {}
        self.bot = Bot(self.configuration.telegram_apikey)
        self.goulash_found = NbdGoulashFound.get()
        for update in self.bot.getUpdates():
            self.process_message(update)

    def temperature(self):
        response = requests.get("http://api.openweathermap.org/data/2.5/weather?id=3435910&units=metric&APPID=%s" % self.configuration.temperature_apikey).json()
        temps = response['main']
        return temps['temp']

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

    def remove_user(self, user, chat_id):
        if user not in self.users.keys():
            self.bot.sendMessage(chat_id=chat_id, text=("No estabas registrado"))
        else:
            self.store.remove_user(user, chat_id)
            del self.users[user]
            self.bot.sendMessage(chat_id=chat_id, text=("Ya no recibirás notificaciones"))

    def unknown_command(self, user, chat_id):
        self.bot.sendMessage(chat_id=chat_id, text='unknown command')

    def process_message(self, update):
        chat_id = update.message.chat_id
        message = update.message.text
        username = str(update.message.from_user.id)

        if message:
            if message.startswith('/subscribe'):
                self.add_user(username, chat_id)
            elif message.startswith('/unsubscribe'):
                self.remove_user(username, chat_id)
            else:
                self.unknown_command(username, chat_id)

        self.last_update_id = update.update_id + 1
        self.store.save_last_update_id(self.last_update_id)

    # Correr periodicamente
    def check_for_messages(self):
        for update in self.bot.getUpdates(offset=self.last_update_id):
            self.process_message(update)

    def goulash(self):
        response = requests.get('http://latropilla.platosdeldia.com/modules.php?name=PDD&func=nick&nick=latropilla')
        body = response.text
        m = re.search(r'([^<>]*(ulash|spaetzle|speciale)[^<>]*)[^$]*(\$[.0-9]*)', body)
        return (m.group(1), m.group(3), self.temperature()) if m else None

    # Correr una vez al dia
    def reset_goulash_flag(self):
        self.goulash_found.save_found(False)

    def goulash_alert(self, found):
        for user in self.users.keys():
            self.bot.sendMessage(chat_id=self.users[user], text=self.build_message(found))

    def build_message(self, found):
        return "HAY %s (%s) [temp: %sC]!!!!" % found

    def ifttt(self, found):
        requests.post("https://maker.ifttt.com/trigger/goulash/with/key/%s" % self.configuration.ifttt_key, data={value1: self.build_message(found)})

    # Correr periodicamente
    def check_for_goulash(self):
        if not NbdGoulashFound.get().read_found():
            found = self.goulash()
            self.goulash_found.save_found(found is not None)
            if found:
                self.ifttt(found)
                self.goulash_alert(found)


app = Flask(__name__)
app.config['DEBUG'] = True

goulash_bot = GoulashBot()
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
