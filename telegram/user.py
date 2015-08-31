#!/usr/bin/env python


import json


class User(object):
    def __init__(self,
                 id,
                 first_name,
                 last_name=None,
                 username=None):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username

    @staticmethod
    def de_json(data):
        return User(id=data.get('id', None),
                    first_name=data.get('first_name', None),
                    last_name=data.get('last_name', None),
                    username=data.get('username', None))

    def to_json(self):
        json_data = {'id': self.id,
                     'first_name': self.first_name}
        if self.last_name:
            json_data['last_name'] = self.last_name
        if self.username:
            json_data['username'] = self.username
        return json.dumps(json_data)

    def __str__(self):
        return self.to_json()
