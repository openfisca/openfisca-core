# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
from builtins import str


# The following variable and the to_unicode function are there to bridge string types across Python 2 & 3
basestring_type = (bytes, str)


def to_unicode(string):
    """
    :param string: a string that needs to be unicoded
    :return: a unicode string
    if the string is a python 2 str type, returns a unicode version of the string.
    """
    if isinstance(string, str):
        return string
    if isinstance(string, bytes):
        return string.decode('utf-8')
    return str(string)


class Dummy(object):
    """A class that does nothing

    Used by function ``empty_clone`` to create an empty instance from an existing object.
    """
    pass


def empty_clone(original):
    """Create a new empty instance of the same class of the original object."""
    new = Dummy()
    new.__class__ = original.__class__
    return new


def stringify_array(array):
    """
        Generate a clean string representation of a NumPY array.
    """
    return '[{}]'.format(', '.join(
        to_unicode(cell)
        for cell in array
        )) if array is not None else 'None'
