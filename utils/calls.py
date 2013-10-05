# -*- coding: utf-8 -*-
"""

"""
import re


def send(patterns, args):
    """

    """
    for pattern, caller in patterns:
        # if the pattern matches the request
        if re.match(pattern, args['request']):
            return caller(*args)
    return None


def upload(env):
    """

    """
    data = {}

    try:
        b = env.get('CONTENT_TYPE', '0')
        b = re.compile('boundary=(.*)').search(b).group(1)
        r = re.compile(b + r"\r\n(.*?)\r\n(.*?)\r\n\r\n(.*?)\r\n--" + b,
                       re.DOTALL)
        s = env['wsgi.input'].read(int(env.get('CONTENT_LENGTH', '0')))
    except:
        return data

    start = 0
    while True:
        m = r.search(s, start)
        if m:
            header = m.group(1).split(';')[1].split('=')[1].replace('"', '')
            data[header] = m.group(3)
            start = m.end() - len(b)
        else:
            break

    return data
