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
            >>> enum_array[0] == Housing.TENANT.index
            True

            # Array of integers

            >>> array = numpy.array([1])
            >>> enum_array = Housing.encode(array)
            >>> enum_array[0] == Housing.TENANT.index
            True

            # Array of bytes

            >>> array = numpy.array([b"TENANT"])
            >>> enum_array = Housing.encode(array)
            >>> enum_array[0] == Housing.TENANT.index
            True

            # Array of strings

            >>> array = numpy.array(["TENANT"])
            >>> enum_array = Housing.encode(array)
            >>> enum_array[0] == Housing.TENANT.index
            True

        .. seealso::
            :meth:`.EnumArray.decode` for decoding.

        """
        if isinstance(array, EnumArray):
            return array

        # String array
        if isinstance(array, numpy.ndarray) and array.dtype.kind in {"U", "S"}:
            array = numpy.select(
                [array == item.name for item in cls],
                [item.index for item in cls],
            ).astype(ENUM_ARRAY_DTYPE)

        # Enum items arrays
        elif isinstance(array, numpy.ndarray) and array.dtype.kind == "O":
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
            if len(array) > 0 and cls.__name__ is array[0].__class__.__name__:
                cls = array[0].__class__

            array = numpy.select(
                [array == item for item in cls],
                [item.index for item in cls],
            ).astype(ENUM_ARRAY_DTYPE)

        return EnumArray(array, cls)


__all__ = ["Enum"]
