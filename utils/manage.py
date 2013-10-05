# -*- coding: utf-8 -*-
import cgi
import cgitb
import traceback
import sys
import os

from pyxmn import utils
from pyxmn.db import conn as db
from pyxmn.utils import language
from pyxmn.utils import calls


cgitb.enable()


class Application(object):
    settings = None

    def __init__(self, settings):
        self.settings = settings
        if settings.DATABASE:
            db.Pool.connect(self.settings)

    def process(self, env, start_response):
        """
        Creates the request environment variable

        """
        if not 'QUERY_STRING' in env or env['QUERY_STRING'] == '':
            req = {'request': ''}
            if sys.argv and len(sys.argv) > 1:
                req = {'request': '-'.join(sys.argv[1:])}
        else:
            if '&' in env['QUERY_STRING']:
                req = dict(map(lambda v: (v.split('=')),
                               env['QUERY_STRING'].split('&')))
            else:
                req = {'request': env['QUERY_STRING']}

        # POST AND UPLOAD
        if 'wsgi.input' in env:
            # @deprecated: sys.upload
            req['sys.upload'] = utils.calls.upload(env)

            post_env = env.copy()
            post_env['QUERY_STRING'] = ''

            posts = cgi.FieldStorage(
                fp=env['wsgi.input'],
                environ=post_env,
                keep_blank_values=True
            )

            for i in posts:
                # MiniFieldStorage
                req[i] = posts[i].value

        response = ''
        debug = ''

        if self.settings.DEBUG:
            debug += 'DEBUG MODE:\n'

            debug += 'ENV:\n'
            for i in env:
                debug += '%s: %s\n' % (i, env[i])

            debug += 'REQ:\n'
            for i in req:
                debug += '%s: %s\n' % (i, req[i])

        # Process the content type
        if 'format' not in req:
            req['format'] = ''

        content_type = self._format_content_type(req['format'])
        req['content-type'] = content_type
        # call action function
        try:
            patterns = ()

            for k, _app in enumerate(self.settings.INSTALLED_APPS):
                exec 'from %s import url as url%s' % (_app, k)
                exec 'patterns += url%s.patterns' % k

            response, template = calls.send(patterns, req)
        except:
            response = 'Message: ' + traceback.format_exc()
            template = open('public/template/error.html').read()

        start_response('200 OK', [('Content-Type', content_type)])

        if template:
            return [
                language.translate(template) % {
                    'content': language.translate(response),
                    'debug': language.translate(debug)
                }
            ]
        else:
            return [response]

    def _format_content_type(self, _format):
        return ('text/json' if _format == 'json' else
                'image/jpeg' if _format == 'image' else
                'text/html')
