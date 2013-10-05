# -*- coding: utf-8 -*-
"""

"""


def define(template_file=''):
    """

    """
    def _template(f):
        """

        """
        def __template(*args):
            template = None
            content_type = args[1] if len(args) > 1 else None

            if content_type == 'text/html':
                template = open(template_file).read()

            return f(*args), template
        return __template
    return _template
