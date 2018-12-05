# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import

import numpy as np
from enum import Enum as BaseEnum

ENUM_ARRAY_DTYPE = np.int16


class Enum(BaseEnum):
    """
        Enum based on `enum34 <https://pypi.python.org/pypi/enum34/>`_, whose items have an index.
    """

    # Tweak enums to add an index attribute to each enum item
    def __init__(self, name):
        # When the enum item is initialized, self._member_names_ contains the names of the previously initialized items, so its length is the index of this item.
        self.index = len(self._member_names_)

    # Bypass the slow Enum.__eq__
    __eq__ = object.__eq__

    __hash__ = object.__hash__  # In Python 3, __hash__ must be defined if __eq__ is defined to stay hashable

    @classmethod
    def encode(cls, array):
        """
            Encode a string numpy array, or an enum item numpy array, into an :any:`EnumArray`. See :any:`EnumArray.decode` for decoding.

            :param numpy.ndarray array: Numpy array of string identifiers, or of enum items, to encode.

            :returns: An :any:`EnumArray` encoding the input array values.
            :rtype: :any:`EnumArray`

            For instance:

            >>> string_identifier_array = numpy.asarray(['free_lodger', 'owner'])
            >>> encoded_array = HousingOccupancyStatus.encode(string_identifier_array)
            >>> encoded_array[0]
            >>> 2  # Encoded value

            >>> enum_item_array = numpy.asarray([HousingOccupancyStatus.free_lodger, HousingOccupancyStatus.owner])
            >>> encoded_array = HousingOccupancyStatus.encode(enum_item_array)
            >>> encoded_array[0]
            >>> 2  # Encoded value

        """
        if type(array) is EnumArray:
            return array
        if array.dtype.kind in {'U', 'S'}:  # String array
            array = np.select([array == item.name for item in cls], [item.index for item in cls]).astype(ENUM_ARRAY_DTYPE)
        elif array.dtype.kind == 'O':  # Enum items arrays
            array = np.select([array == item for item in cls], [item.index for item in cls]).astype(ENUM_ARRAY_DTYPE)
        return EnumArray(array, cls)


class EnumArray(np.ndarray):
    """
        Numpy array subclass representing an array of enum items.

        EnumArrays are encoded as ``int`` arrays to improve performance
    """

    # Subclassing np.ndarray is a little tricky. To read more about the two following methods, see https://docs.scipy.org/doc/numpy-1.13.0/user/basics.subclassing.html#slightly-more-realistic-example-attribute-added-to-existing-array.
    def __new__(cls, input_array, possible_values = None):
        obj = np.asarray(input_array).view(cls)
        obj.possible_values = possible_values
        return obj

    # See previous comment
    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.possible_values = getattr(obj, 'possible_values', None)

    def __eq__(self, other):
        # When comparing to an item of self.possible_values, use the item index to speed up the comparison
        if other.__class__ is self.possible_values:
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
            >>> <HousingOccupancyStatus.free_lodger: 'Free lodger'>  # Decoded value : enum item
        """
        return np.select([self == item.index for item in self.possible_values], [item for item in self.possible_values])

    def decode_to_str(self):
        """
            Return the array of string identifiers corresponding to self

            >>> enum_array = household('housing_occupancy_status', period)
            >>> enum_array[0]
            >>> 2  # Encoded value
            >>> enum_array.decode_to_str()[0]
            >>> 'free_lodger' # String identifier
        """
        return np.select([self == item.index for item in self.possible_values], [item.name for item in self.possible_values])

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, str(self.decode()))
