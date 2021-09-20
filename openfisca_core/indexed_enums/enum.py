from __future__ import annotations

import enum
from typing import Any, Union

import numpy

from openfisca_core.types import ArrayType, Encodable

from .. import indexed_enums as enums
from .enum_array import EnumArray

A = Union[
    EnumArray,
    ArrayType[Encodable],
    ArrayType[bytes],
    ArrayType[int],
    ArrayType[str],
    ]


class Enum(enum.Enum):
    """Enum based on `enum34 <https://pypi.python.org/pypi/enum34/>`_.

    Whose items have an :obj:`int` index. This is useful and performant when
    running simulations on large populations.

    Attributes:
        index (:obj:`int`): The ``index`` of the :class:`.Enum` member.
        name (:obj:`str`): The ``name`` of the :class:`.Enum` member.
        value: The ``value`` of the :class:`.Enum` member.

    Examples:
        >>> class Housing(Enum):
        ...     OWNER = "Owner"
        ...     TENANT = "Tenant"
        ...     FREE_LODGER = "Free lodger"
        ...     HOMELESS = "Homeless"

        >>> repr(Housing)
        "<enum 'Housing'>"

        >>> repr(Housing.TENANT)
        '<Housing.TENANT(Tenant)>'

        >>> str(Housing.TENANT)
        'Housing.TENANT'

        >>> dict([(Housing.TENANT, Housing.TENANT.value)])
        {<Housing.TENANT(Tenant)>: 'Tenant'}

        >>> list(Housing)
        [<Housing.OWNER(Owner)>, <Housing.TENANT(Tenant)>, ...]

        >>> Housing["TENANT"]
        <Housing.TENANT(Tenant)>

        >>> Housing("Tenant")
        <Housing.TENANT(Tenant)>

        >>> Housing.TENANT in Housing
        True

        >>> len(Housing)
        4

        >>> Housing.TENANT == Housing.TENANT
        True

        >>> Housing.TENANT != Housing.TENANT
        False

        >>> Housing.TENANT > Housing.TENANT
        False

        >>> Housing.TENANT < Housing.TENANT
        False

        >>> Housing.TENANT >= Housing.TENANT
        True

        >>> Housing.TENANT <= Housing.TENANT
        True

        >>> Housing.TENANT.index
        1

        >>> Housing.TENANT.name
        'TENANT'

        >>> Housing.TENANT.value
        'Tenant'

    """

    index: int
    name: str
    value: Any

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

            >>> array = numpy.array([[1, 2], [3, 4]])
            >>> array[MyEnum.bar.index]
            array([3, 4])

        """

        self.index = len(self._member_names_)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}.{self.name}({self.value})>"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Enum):
            return NotImplemented

        return self.index < other.index

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Enum):
            return NotImplemented

        return self.index <= other.index

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Enum):
            return NotImplemented

        return self.index > other.index

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Enum):
            return NotImplemented

        return self.index >= other.index

    __eq__ = object.__eq__
    """Bypass the slow :meth:`~enum.Enum.__eq__`."""

    __hash__ = object.__hash__
    """:meth:`.__hash__` must also be defined as so to stay hashable."""

    @classmethod
    def encode(cls, array: A) -> EnumArray:
        """Encodes an encodable array into an :obj:`.EnumArray`.

        Args:
            array: Array to encode.

        Returns:
            :obj:`.EnumArray`: An :obj:`array <.EnumArray>` with the encoded
            input values.

        Examples:
            >>> class MyEnum(Enum):
            ...     foo = b"foo"
            ...     bar = b"bar"

            # EnumArray

            >>> array = numpy.array([1])
            >>> enum_array = EnumArray(array, MyEnum)
            >>> MyEnum.encode(enum_array)
            <EnumArray([<MyEnum.bar(b'bar')>])>

            # ArrayTipe[Enum]

            >>> array = numpy.array([MyEnum.bar])
            >>> enum_array = MyEnum.encode(array)
            >>> enum_array[0] == MyEnum.bar.index
            True

            # ArrayType[bytes]

            >>> array = numpy.array([b"bar"])
            >>> enum_array = MyEnum.encode(array)
            >>> enum_array[0] == MyEnum.bar.index
            True

            # ArrayType[int]

            >>> array = numpy.array([1])
            >>> enum_array = MyEnum.encode(array)
            >>> enum_array[0] == MyEnum.bar.index
            True

            # ArrayType[str]

            >>> array = numpy.array(["bar"])
            >>> enum_array = MyEnum.encode(array)
            >>> enum_array[0] == MyEnum.bar.index
            True

        .. versionchanged:: 35.8.0
            Fixed a bug when encoding :class:`bytes` arrays, now they're casted
            to :obj:`str` prior to encoding.

        .. versionchanged:: 35.8.0
            Fixed a bug when encoding scalar arrays of :class:`.Enum` items,
            now they're encoded as expected.

        .. seealso::
            :meth:`.EnumArray.decode` for decoding.

        """

        if isinstance(array, EnumArray):

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

        return EnumArray(array, cls)
