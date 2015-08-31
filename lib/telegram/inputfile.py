#!/usr/bin/env python


import mimetools
import mimetypes
import os
import urllib2


class InputFile(object):
    def __init__(self,
                 data):
        self.data = data
        self.boundary = mimetools.choose_boundary()

        if 'audio' in data:
            self.input_name = 'audio'
            self.input_file = data.pop('audio')
        if 'document' in data:
            self.input_name = 'document'
            self.input_file = data.pop('document')
        if 'photo' in data:
            self.input_name = 'photo'
            self.input_file = data.pop('photo')
        if 'video' in data:
            self.input_name = 'video'
            self.input_file = data.pop('video')

        if isinstance(self.input_file, file):
            self.filename = os.path.basename(self.input_file.name)
            self.input_file_content = self.input_file.read()
        if 'http' in self.input_file:
            self.filename = os.path.basename(self.input_file)
            self.input_file_content = urllib2.urlopen(self.input_file).read()

        self.mimetype = mimetypes.guess_type(self.filename)[0] or \
            'application/octet-stream'

    @property
    def headers(self):
        return {'User-agent': 'Python Telegram Bot (https://github.com/leandrotoledo/python-telegram-bot)',
                'Content-type': self.content_type}

    @property
    def content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def to_form(self):
        form = []
        form_boundary = '--' + self.boundary

        # Add data fields
        for name, value in self.data.iteritems():
            form.extend([
                form_boundary,
                str('Content-Disposition: form-data; name="%s"' % name),
                '',
                str(value)
            ])

        # Add input_file to upload
        form.extend([
            form_boundary,
            str('Content-Disposition: form-data; name="%s"; filename="%s"' % (
                self.input_name, self.filename
            )),
            'Content-Type: %s' % self.mimetype,
            '',
            self.input_file_content
        ])

        form.append('--' + self.boundary + '--')
        form.append('')

        return '\r\n'.join(form)
