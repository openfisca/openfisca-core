# -*- coding: utf-8 -*-


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
    """Generate a clean string representation of a NumPY array.
    """
    return u'[{}]'.format(u', '.join(
        unicode(cell)
        for cell in array
        )) if array is not None else u'None'
