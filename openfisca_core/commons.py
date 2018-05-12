# -*- coding: utf-8 -*-

# The following two variables and the is_unicode function are there to bridge string types across Python 2 & 3
unicode_type = u"".__class__
basestring_type = (b"".__class__, unicode_type)


def to_unicode(string):
    """
    :param string: a string that needs to be unicoded
    :param encoding: a string that represent the encoding type
    :return: a unicode string
    if the string is a python 2 str type, returns a unicode version of the string.
    """
    if not isinstance(string, basestring_type):
        string = str(string)
    if isinstance(string, unicode_type):
        return string

    # Next line only gets triggered if the code is run in python 2
    return string.decode('utf-8')


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
    return u'[{}]'.format(u', '.join(
        to_unicode(cell)
        for cell in array
        )) if array is not None else u'None'
