from __future__ import annotations

import enum
from typing import Union

import numpy

from openfisca_core.types import ArrayLike, ArrayType

from .. import indexed_enums as enums

#: Type of any encodable array.
Encodable = Union[
    enums.EnumArray,
    ArrayLike["Enum"],
    ArrayType[bytes],
    ArrayType[int],
    ArrayType[str],
    ]


class Enum(enum.Enum):
    """Enum based on `enum34 <https://pypi.python.org/pypi/enum34/>`_.

    Whose items have an :obj:`int` index. This is useful and performant when
    running simulations on large populations.

    Examples:
        >>> class Housing(Enum):
        ...     owner = "Owner"
        ...     tenant = "Tenant"
        ...     free_lodger = "Free lodger"
        ...     homeless = "Homeless"

        >>> Housing
        <enum 'Housing'>

        >>> list(Housing)
        [<Housing.owner: 'Owner'>, ...]

        >>> len(Housing)
        4

        >>> Housing.tenant
        <Housing.tenant: 'Tenant'>

        >>> Housing["tenant"]
        <Housing.tenant: 'Tenant'>

        >>> Housing.tenant.index
        1

        >>> Housing.tenant.name
        'tenant'

        >>> Housing.tenant.value
        'Tenant'

    """

    def __init__(self, name: str) -> None:
        """ Tweaks :class:`~enum.Enum` to add an index to each enum item.

        When the enum item is initialized, ``self._member_names_`` contains the
        names of the previously initialized items, so its length is the index
        of this item.

        Args:
            name: The name of the enum.

        Examples:
            >>> MyEnum = Enum("MyEnum", "foo bar")
            >>> MyEnum.bar.index
            1

            >>> class MyEnum(Enum):
            ...     foo = b"foo"
            ...     bar = b"bar"

            >>> MyEnum.bar.index
            1

        """

        self.index = len(self._member_names_)

    #: Bypass the slow :meth:`~enum.Enum.__eq__`.
    __eq__ = object.__eq__

    #: :meth:`.__hash__` must also be defined as so to stay hashable.
    __hash__ = object.__hash__

    @classmethod
    def encode(cls, array: Encodable) -> enums.EnumArray:
        """Encodes an :class:`.Encodable` array into an :class:`.EnumArray.`

        Args:
            array: Array to encode.

        Returns:
            An array with the encoded input values.

        Examples:
            >>> class MyEnum(Enum):
            ...     foo = b"foo"
            ...     bar = b"bar"

            # EnumArray

            >>> array = numpy.array([1])
            >>> enum_array = enums.EnumArray(array, MyEnum)
            >>> MyEnum.encode(enum_array)
            EnumArray([<MyEnum.bar: b'bar'>])

            # ArrayLike["Enum"]

            >>> array = numpy.array([MyEnum.bar])
            >>> enum_array = MyEnum.encode(array)
            >>> enum_array[0] == MyEnum.bar.index
            True

            # ArrayLike[bytes]

            >>> array = numpy.array([b"bar"])
            >>> enum_array = MyEnum.encode(array)
            >>> enum_array[0] == MyEnum.bar.index
            True

            # ArrayLike[int]

            >>> array = numpy.array([1])
            >>> enum_array = MyEnum.encode(array)
            >>> enum_array[0] == MyEnum.bar.index
            True

            # ArrayLike[str]

            >>> array = numpy.array(["bar"])
            >>> enum_array = MyEnum.encode(array)
            >>> enum_array[0] == MyEnum.bar.index
            True

        .. versionchanged:: 35.5.0
            Fixed a bug when encoding :class:`bytes` arrays, now they're casted
            to :obj:`str` prior to encoding.

        .. versionchanged:: 35.5.0
            Fixed a bug when encoding scalar arrays of :class:`.Enum` items,
            now they're encoded as expected.

        .. seealso::
            :meth:`.EnumArray.decode` for decoding.

        """

        if isinstance(array, enums.EnumArray):

            return array

        if isinstance(array, numpy.ndarray) and \
           array.size > 0 and \
           isinstance(array.take(0), (Enum, bytes, str)):

            if numpy.issubdtype(array.dtype, bytes):

                array = array.astype(str)

            if numpy.issubdtype(array.dtype, str):

                conditions = [array == item.name for item in cls]

            if numpy.issubdtype(array.dtype, cls):

                # Ensure we are comparing the comparable.
                #
                # The problem this fixes:
                #
                # On entering this method "cls" will generally come from
                # variable.possible_values, while the array values may come
                # from directly importing a module containing an Enum class.
                #
                # However, variables (and hence their possible_values) are
                # loaded by a call to load_module, which gives them a different
                # identity from the ones imported in the usual way.
                #
                # So, instead of relying on the "cls" passed in, we use only
                # its name to check that the values in the array, if non-empty,
                # are of the right type.

                cls = array.take(0).__class__
                conditions = [array == item for item in cls]

            choices = [item.index for item in cls]

            array = \
                numpy \
                .select(conditions, choices) \
                .astype(enums.ENUM_ARRAY_DTYPE)

        return enums.EnumArray(array, cls)
