from __future__ import annotations


import numpy

from .enum_array import EnumArray
from .config import ENUM_ARRAY_DTYPE
from . import types as t


class Enum(t.Enum):
    """Enum based on `enum34 <https://pypi.python.org/pypi/enum34/>`_.

    Its items have an :class:`int` index, useful and performant when running
    :mod:`~openfisca_core.simulations` on large :mod:`~openfisca_core.populations`.

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

    #: The :attr:`index` of the :class:`.Enum` member.
    index: int

    def __init__(self, *__args: object, **__kwargs: object) -> None:
        """Tweak :class:`enum.Enum` to add an :attr:`.index` to each enum item.

        When the enum is initialised, ``_member_names_`` contains the names of
        the already initialized items, so its length is the index of this item.

        Args:
            *__args: Positional arguments.
            **__kwargs: Keyword arguments.

        Note:
            ``_member_names_`` is undocumented in upstream :class:`enum.Enum`.

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
        return f"{self.__class__.__name__}.{self.name}({self.value})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Enum):
            return NotImplemented
        return self.index == other.index

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, Enum):
            return NotImplemented
        return self.index != other.index

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

    #: :meth:`.__hash__` must also be defined so as to stay hashable.
    __hash__ = object.__hash__

    @classmethod
    def encode(
        cls,
        array: EnumArray | numpy.int32 | numpy.float32 | numpy.object_,
    ) -> EnumArray:
        """Encode an encodable array into an :class:`.EnumArray`.

        Args:
            array: :class:`~numpy.ndarray` to encode.

        Returns:
            EnumArray: An :class:`.EnumArray` with the encoded input values.

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

        .. seealso::
            :meth:`.EnumArray.decode` for decoding.

        """
        conditions: list[t.Array[t.DTypeBool]]
        choices: list[int]

        if isinstance(array, EnumArray):

            return array

        if (
            isinstance(array, numpy.ndarray)
            and array.size > 0
            and isinstance(array.take(0), (Enum, bytes, str))
        ):

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

            array = numpy.select(conditions, choices).astype(ENUM_ARRAY_DTYPE)

        return EnumArray(array, cls)


__all__ = ["Enum"]
