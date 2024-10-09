from __future__ import annotations

import numpy

from . import types as t
from ._enum_type import EnumType
from ._type_guards import _is_int_array, _is_str_array
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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Enum):
            return NotImplemented
        return self.index == other.index

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, Enum):
            return NotImplemented
        return self.index != other.index

    def __hash__(self) -> int:
        return hash(self.index)

    @classmethod
    def encode(
        cls,
        array: (
            EnumArray
            | t.IntArray
            | t.StrArray
            | t.ObjArray
            | t.ArrayLike[int]
            | t.ArrayLike[str]
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
            EnumArray(Housing.TENANT)

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
            TypeError: Failed to encode "[b'TENANT']" of type 'bytes_', as i...

        .. seealso::
            :meth:`.EnumArray.decode` for decoding.

        """
        if isinstance(array, EnumArray):
            return array

        if not isinstance(array, numpy.ndarray):
            return cls.encode(numpy.array(array))

        if array.size == 0:
            return EnumArray(numpy.array([]), cls)

        if array.ndim == 0:
            msg = (
                "Scalar arrays are not supported: expecting a vector array, "
                f"instead. Please try again with `numpy.array([{array}])`."
            )
            raise TypeError(msg)

        # Integer array
        if _is_int_array(array):
            indices = numpy.array(array[array < len(cls.items)], dtype=t.EnumDType)
            return EnumArray(indices, cls)

        # String array
        if _is_str_array(array):
            indices = cls.items[numpy.isin(cls.names, array)].index
            return EnumArray(indices, cls)

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
            indices = cls.items[numpy.isin(cls.enums, array)].index
            return EnumArray(indices, cls)

        msg = (
            f"Failed to encode \"{array}\" of type '{array[0].__class__.__name__}', "
            "as it is not supported. Please, try again with an array of "
            f"'{int.__name__}', '{str.__name__}', or '{cls.__name__}'."
        )
        raise TypeError(msg)


__all__ = ["Enum"]
