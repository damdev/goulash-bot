#!/usr/bin/env python


import json


class Video(object):
    def __init__(self,
                 file_id,
                 width,
                 height,
                 duration,
                 thumb,
                 mime_type=None,
                 file_size=None,
                 caption=None):
        self.file_id = file_id
        self.width = width
        self.height = height
        self.duration = duration
        self.thumb = thumb
        self.mime_type = mime_type
        self.file_size = file_size
        self.caption = caption

    @staticmethod
    def de_json(data):
        if 'thumb' in data:
            from telegram import PhotoSize
            thumb = PhotoSize.de_json(data['thumb'])
        else:
            thumb = None

        return Video(file_id=data.get('file_id', None),
                     width=data.get('width', None),
                     height=data.get('height', None),
                     duration=data.get('duration', None),
                     thumb=thumb,
                     mime_type=data.get('mime_type', None),
                     file_size=data.get('file_size', None),
                     caption=data.get('caption', None))

    def to_json(self):
        json_data = {'file_id': self.file_id,
                     'width': self.width,
                     'height': self.height,
                     'duration': self.duration,
                     'thumb': self.thumb.to_json()}
        if self.mime_type:
            json_data['mime_type'] = self.mime_type
        if self.file_size:
            json_data['file_size'] = self.file_size
        if self.caption:
            json_data['caption'] = self.caption
        return json.dumps(json_data)

    def __str__(self):
        return self.to_json()
