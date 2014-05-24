# -*- coding: utf-8 -*-
APP_ROOT = '.'
VERSION = (0, 1, 9, )


def get_version():
    """
    :returns: a string representation of current version.
    :rtype: :class:`str`
    """
    return '.'.join([str(x) for x in VERSION])


def version_lt(a, b):
    """
    Check if one version is less than another.

    :param tuple a: a version to check.
    :param tuple b: a version to compare with.

    :returns: ``True`` if version ``a`` is less than version ``b``.
    :rtype: :class:`bool`
    """
    major_a, minor_a, patch_a = a
    major_b, minor_b, patch_b = b

    if major_a < major_b:
        return True
    if major_a > major_b:
        return False

    if minor_a < minor_b:
        return True
    if minor_a > minor_b:
        return False

    return patch_a < patch_b
