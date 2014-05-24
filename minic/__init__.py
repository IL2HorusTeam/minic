# -*- coding: utf-8 -*-
APP_ROOT = '.'
VERSION = (0, 1, 9, )


def get_version():
    """
    :returns: a string representation of current version.
    :rtype: :class:`str`
    """
    return '.'.join([str(x) for x in VERSION])
