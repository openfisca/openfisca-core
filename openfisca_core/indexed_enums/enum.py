from __future__ import annotations

from collections.abc import Sequence

import numpy

from . import types as t
from ._enum_type import EnumType
from ._errors import EnumEncodingError, EnumMemberNotFoundError
from ._guards import (
    _is_enum_array,
    _is_enum_array_like,
    _is_int_array,
    _is_int_array_like,
    _is_str_array,
    _is_str_array_like,
)
from ._utils import _enum_to_index, _int_to_index, _str_to_index
from .enum_array import EnumArray


class Enum(t.Enum, metaclass=EnumType):
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
        'Housing.TENANT'

        >>> str(Housing.TENANT)
        'Housing.TENANT'

        >>> dict([(Housing.TENANT, Housing.TENANT.value)])
        {Housing.TENANT: 'Tenant'}

        >>> list(Housing)
        [Housing.OWNER, Housing.TENANT, Housing.FREE_LODGER, Housing.HOMELESS]

        >>> Housing["TENANT"]
        Housing.TENANT

        >>> Housing("Tenant")
        Housing.TENANT

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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"

    @classmethod
    def encode(cls, array: t.VarArray | t.ArrayLike[object]) -> t.EnumArray:
        """Encode an encodable array into an :class:`.EnumArray`.

        Args:
            array: :class:`~numpy.ndarray` to encode.

        Returns:
            EnumArray: An :class:`.EnumArray` with the encoded input values.

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
            EnumArray([Housing.TENANT])

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
            >>> enum_array == Housing.TENANT
            array([ True])

            # Array of bytes

            >>> array = numpy.array([b"TENANT"])
            >>> enum_array = Housing.encode(array)
            Traceback (most recent call last):
            EnumEncodingError: Failed to encode "[b'TENANT']" of type 'bytes...

        .. seealso::
            :meth:`.EnumArray.decode` for decoding.

        """
        if isinstance(array, EnumArray):
            return array
        if len(array) == 0:
            return EnumArray(numpy.asarray(array, t.EnumDType), cls)
        if isinstance(array, Sequence):
            return cls._encode_array_like(array)
        return cls._encode_array(array)

    @classmethod
    def _encode_array(cls, value: t.VarArray) -> t.EnumArray:
        if _is_int_array(value):
            indices = _int_to_index(cls, value)
        elif _is_str_array(value):  # type: ignore[unreachable]
            indices = _str_to_index(cls, value)
        elif _is_enum_array(value) and cls == value[0].__class__:
            indices = _enum_to_index(value)
        else:
            raise EnumEncodingError(cls, value)
        if indices.size != len(value):
            raise EnumMemberNotFoundError(cls)
        return EnumArray(indices, cls)

    @classmethod
    def _encode_array_like(cls, value: t.ArrayLike[object]) -> t.EnumArray:
        if _is_int_array_like(value):
            indices = _int_to_index(cls, value)
        elif _is_str_array_like(value):  # type: ignore[unreachable]
            indices = _str_to_index(cls, value)
        elif _is_enum_array_like(value):
            indices = _enum_to_index(value)
        else:
            raise EnumEncodingError(cls, value)
        if indices.size != len(value):
            raise EnumMemberNotFoundError(cls)
        return EnumArray(indices, cls)


__all__ = ["Enum"]
