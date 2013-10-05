# -*- coding: utf-8 -*-
import os
import os.path
import gettext
import re


def setup(settings):
    """

    """
    LOCALE_DIR = localedir = os.path.join(settings.path('root'), 'locale')

    gettext.install(settings.TRANSLATION_DOMAIN, LOCALE_DIR, unicode=True)

    if 'HTTP_ACCEPT_LANGUAGE' in os.environ:
        request_lang = os.environ['HTTP_ACCEPT_LANGUAGE'][:2]
    else:
        request_lang = os.environ['LANG'][:2]

    if request_lang not in settings.LANGUAGES:
        gettext.install(
            settings.TRANSLATION_DOMAIN,
            localedir=os.path.join(settings.path('root'), 'locale')
        )
    else:
        gettext_lang = gettext.translation(
            settings.TRANSLATION_DOMAIN,
            localedir=os.path.join(settings.path('root'), 'locale'),
            languages=[request_lang]
        )
        gettext_lang.install()


def translate(text):
    pattern = '\{\%\s*trans\s+"([^}]*)"\s*\%\}'
    pattern_replace = ['\{\%\s*trans\s+"', '', '"\s*\%\}']

    c = re.compile(pattern)
    for i in c.findall(text):
        pattern_replace[1] = re.escape(i)
        text = re.sub(r''.join(pattern_replace), _(i), text)

    return text


def prepare(settings):
    # prepare html
    lang_pot = '%s/locale/%s.pot' % (
        settings.path('root'), settings.TRANSLATION_DOMAIN
    )

    pot_content = open(lang_pot).read()

    exp = re.compile('\{\%\s*trans\s+"([^}]*)"\s*\%\}')

    for root, subFolders, files in os.walk(settings.path('root') + 'public'):
        for _file in files:
            header = _file
            text = open(os.path.join(root, _file)).read()
            for tag in exp.findall(text):
                pattern = 'msgid "%s"' % tag
                if pattern not in pot_content:
                    if header:
                        pot_content += '\n#: %s/%s' % (root, header)
                        header = None
                    pot_content += '\nmsgid "%s"\n' % tag
                    pot_content += 'msgstr ""\n'

    open(lang_pot, 'w').write(pot_content)

    c_xgettext = (
        'xgettext --default-domain=%(domain)s' +
        ' --output=locale/%(domain)s.pot *.py '
    )
    c = c_xgettext % {'domain':  settings.TRANSLATION_DOMAIN}
    out = os.popen(c).read()
    print(out)

    c_msgmerge = (
        'msgmerge --output-file=locale/%(lang)s/%(domain)s.po' +
        ' locale/%(lang)s/%(domain)s.po locale/%(domain)s.pot'
    )

    c_msgfmt = (
        'msgfmt --output-file=locale/%(lang)s/LC_MESSAGES/%(domain)s.mo' +
        ' locale/%(lang)s/%(domain)s.po'
    )

    for lang in settings.LANGUAGES:
        print lang
        c = c_msgmerge % {
            'domain': settings.TRANSLATION_DOMAIN,
            'lang': lang
        }
        out = os.popen(c).read()
        print(out)

        c = c_msgfmt % {
            'domain': settings.TRANSLATION_DOMAIN,
            'lang': lang
        }
        out = os.popen(c).read()
        print(out)

    return
