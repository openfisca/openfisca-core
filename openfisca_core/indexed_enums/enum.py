from __future__ import annotations

import numpy

from . import types as t
from .config import ENUM_ARRAY_DTYPE
from .enum_array import EnumArray


class Enum(t.Enum):
    """Enum based on `enum34 <https://pypi.python.org/pypi/enum34/>`_.

    Its items have an :class:`int` index, useful and performant when running
    :mod:`~openfisca_core.simulations` on large :mod:`~openfisca_core.populations`.

    Examples:
        >>> from openfisca_core import indexed_enums as enum

        >>> class Housing(enum.Enum):
        ...     OWNER = "Owner"
        ...     TENANT = "Tenant"
        ...     FREE_LODGER = "Free lodger"
        ...     HOMELESS = "Homeless"

        >>> repr(Housing)
        "<enum 'Housing'>"

        >>> repr(Housing.TENANT)
        "<Housing.TENANT: 'Tenant'>"

        >>> str(Housing.TENANT)
        'Housing.TENANT'

        >>> dict([(Housing.TENANT, Housing.TENANT.value)])
        {<Housing.TENANT: 'Tenant'>: 'Tenant'}

        >>> list(Housing)
        [<Housing.OWNER: 'Owner'>, <Housing.TENANT: 'Tenant'>, ...]

        >>> Housing["TENANT"]
        <Housing.TENANT: 'Tenant'>

        >>> Housing("Tenant")
        <Housing.TENANT: 'Tenant'>

        >>> Housing.TENANT in Housing
        True

        >>> len(Housing)
        4

        >>> Housing.TENANT == Housing.TENANT
        True

        >>> Housing.TENANT != Housing.TENANT
        False

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

        Examples:
            >>> import numpy

            >>> from openfisca_core import indexed_enums as enum

            >>> Housing = enum.Enum("Housing", "owner tenant")
            >>> Housing.tenant.index
            1

            >>> class Housing(enum.Enum):
            ...     OWNER = "Owner"
            ...     TENANT = "Tenant"

            >>> Housing.TENANT.index
            1

            >>> array = numpy.array([[1, 2], [3, 4]])
            >>> array[Housing.TENANT.index]
            array([3, 4])

        Note:
            ``_member_names_`` is undocumented in upstream :class:`enum.Enum`.

        """
        self.index = len(self._member_names_)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Enum):
            return NotImplemented
        return self.index == other.index

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, Enum):
            return NotImplemented
        return self.index != other.index

    #: :meth:`.__hash__` must also be defined so as to stay hashable.
    __hash__ = object.__hash__

    @classmethod
    def encode(
        cls,
        array: (
            EnumArray
            | t.Array[t.DTypeStr]
            | t.Array[t.DTypeInt]
            | t.Array[t.DTypeEnum]
            | t.Array[t.DTypeObject]
            | t.ArrayLike[str]
            | t.ArrayLike[int]
            | t.ArrayLike[t.Enum]
        ),
    ) -> EnumArray:
        """Encode an encodable array into an :class:`.EnumArray`.

        Args:
            array: :class:`~numpy.ndarray` to encode.

        Returns:
            EnumArray: An :class:`.EnumArray` with the encoded input values.

        Raises:
            TypeError: If ``array`` is a scalar :class:`~numpy.ndarray`.
            TypeError: If ``array`` is of a diffent :class:`.Enum` type.
            NotImplementedError: If ``array`` is of an unsupported type.

        Examples:
            >>> import numpy

            >>> from openfisca_core import indexed_enums as enum

            >>> class Housing(enum.Enum):
            ...     OWNER = "Owner"
            ...     TENANT = "Tenant"

            # EnumArray

            >>> array = numpy.array([1])
            >>> enum_array = enum.EnumArray(array, Housing)
            >>> Housing.encode(enum_array)
            EnumArray([<Housing.TENANT: 'Tenant'>])

            # Array of Enum

            >>> array = numpy.array([Housing.TENANT])
            >>> enum_array = Housing.encode(array)
            >>> enum_array == Housing.TENANT
            array([ True])

            # Array of integers

            >>> array = numpy.array([1])
            >>> enum_array = Housing.encode(array)
            >>> enum_array == Housing.TENANT
            array([ True])

            # Array of strings

            >>> array = numpy.array(["TENANT"])
            >>> enum_array = Housing.encode(array)
            >>> enum_array[0] == Housing.TENANT.index
            True

            # Array of bytes

            >>> array = numpy.array([b"TENANT"])
            >>> enum_array = Housing.encode(array)
            Traceback (most recent call last):
            NotImplementedError: Unsupported encoding: bytes48.

        .. seealso::
            :meth:`.EnumArray.decode` for decoding.

        """
        if isinstance(array, EnumArray):
            return array

        if not isinstance(array, numpy.ndarray):
            return cls.encode(numpy.array(array))

        if array.size == 0:
            return EnumArray(array, cls)

        if array.ndim == 0:
            msg = (
                "Scalar arrays are not supported: expecting a vector array, "
                f"instead. Please try again with `numpy.array([{array}])`."
            )
            raise TypeError(msg)

        # Enum data type array
        if numpy.issubdtype(array.dtype, t.DTypeEnum):
            indexes = numpy.array([item.index for item in cls], t.DTypeEnum)
            return EnumArray(indexes[array[array < indexes.size]], cls)

        # Integer array
        if numpy.issubdtype(array.dtype, int):
            array = numpy.array(array, dtype=t.DTypeEnum)
            return cls.encode(array)

        # String array
        if numpy.issubdtype(array.dtype, t.DTypeStr):
            enums = [cls.__members__[key] for key in array if key in cls.__members__]
            return cls.encode(enums)

        # Enum items arrays
        if numpy.issubdtype(array.dtype, t.DTypeObject):
            # Ensure we are comparing the comparable. The problem this fixes:
            # On entering this method "cls" will generally come from
            # variable.possible_values, while the array values may come from
            # directly importing a module containing an Enum class. However,
            # variables (and hence their possible_values) are loaded by a call
            # to load_module, which gives them a different identity from the
            # ones imported in the usual way.
            #
            # So, instead of relying on the "cls" passed in, we use only its
            # name to check that the values in the array, if non-empty, are of
            # the right type.
            if cls.__name__ is array[0].__class__.__name__:
                array = numpy.select(
                    [array == item for item in array[0].__class__],
                    [item.index for item in array[0].__class__],
                ).astype(ENUM_ARRAY_DTYPE)
                return EnumArray(array, cls)

            msg = (
                f"Diverging enum types are not supported: expected {cls.__name__}, "
                f"but got {array[0].__class__.__name__} instead."
            )
            raise TypeError(msg)

        msg = f"Unsupported encoding: {array.dtype.name}."
        raise NotImplementedError(msg)


__all__ = ["Enum"]
