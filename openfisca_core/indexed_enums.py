# -*- coding: utf-8 -*-

import numpy as np
from enum import Enum as BaseEnum


class EnumArray(np.ndarray):
    """
        Numpy array subclass representing an array of enum items.

        EnumArrays are encoded as int arrays to improve performance
    """

    dtype = np.int16

    # Subclassing np.ndarray is a little tricky. To read more about the two following methods, see https://docs.scipy.org/doc/numpy-1.13.0/user/basics.subclassing.html#slightly-more-realistic-example-attribute-added-to-existing-array.
    def __new__(cls, input_array, enum = None):
        obj = np.asarray(input_array).view(cls)
        obj.enum = enum
        return obj

    # See previous comment
    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.enum = getattr(obj, 'enum', None)

    def __eq__(self, other):
        # When comparing to an item of self.enum, use the item index to speed up the comparison
        if other.__class__ is self.enum:
            return self.view(np.ndarray) == other.index  # use view(np.ndarray) so that the result is a classic ndarray, not an EnumArray
        return self.view(np.ndarray) == other

    def __ne__(self, other):
        return np.logical_not(self == other)

    def _forbidden_operation(self, other):
        raise TypeError("Forbidden operation. The only operations allowed on EnumArrays are '==' and '!='.")

    __add__ = _forbidden_operation
    __mul__ = _forbidden_operation
    __lt__ = _forbidden_operation
    __le__ = _forbidden_operation
    __gt__ = _forbidden_operation
    __ge__ = _forbidden_operation
    __and__ = _forbidden_operation
    __or__ = _forbidden_operation

    def decode(self):
        """
            Return the array of enum items corresponding to self

            >>> enum_array = household('housing_occupancy_status', period)
            >>> enum_array[0]
            >>> 2  # Encoded value
            >>> enum_array.decode()[0]
            >>> <HousingOccupancyStatus.free_lodger: u'Free logder'>  # Decoded value
        """
        return np.select([self == item.index for item in self.enum], [item for item in self.enum])

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, str(self.decode()))


class Enum(BaseEnum):
    # Tweak enums to add an index attribute to each enum item
    def __init__(self, name):
        # When the enum item is initialized, self._member_names_ contains the names of the previously initialized items, so its length is the index of this item.
        self.index = len(self._member_names_)

    # Bypass the slow Enum.__eq__
    __eq__ = object.__eq__

    @classmethod
    def encode(cls, array):
        if type(array) is EnumArray:
            return array
        if array.dtype.kind in {'U', 'S'}:  # String array
            array = np.select([array == item.name for item in cls], [item.index for item in cls]).astype(EnumArray.dtype)
        elif array.dtype.kind == 'O':  # Enum items arrays
            array = np.select([array == item for item in cls], [item.index for item in cls]).astype(EnumArray.dtype)
        return EnumArray(array, cls)
