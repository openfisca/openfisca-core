from __future__ import annotations

import numpy

from . import types as t
from .config import ENUM_ARRAY_DTYPE
from .enum_array import EnumArray


class Enum(t.Enum):
    """Enum based on `enum34 <https://pypi.python.org/pypi/enum34/>`_.

    Its items have an :any:`int` index. This is useful and performant when
    running simulations on large populations.

    """

    #: The ``index`` of the ``Enum`` member.
    index: int

    def __init__(self, *__args: object, **__kwargs: object) -> None:
        """Tweak :any:`~enum.Enum` to add an index to each enum item.

        When the enum is initialised, ``_member_names_`` contains the names of
        the already initialized items, so its length is the index of this item.

        Args:
            *__args: Positional arguments.
            **__kwargs: Keyword arguments.

        """

        self.index = len(self._member_names_)

    #: Bypass the slow :any:`~enum.Enum.__eq__` method.
    __eq__ = object.__eq__

    #: :meth:`.__hash__` must also be defined so as to stay hashable.
    __hash__ = object.__hash__

    @classmethod
    def encode(
        cls,
        array: EnumArray | numpy.int32 | numpy.float32 | numpy.object_,
    ) -> EnumArray:
        """Encode an encodable array into an ``EnumArray``.

        Args:
            array: Array to encode.

        Returns:
            EnumArray: An ``EnumArray`` with the encoded input values.

        For instance:

        >>> string_identifier_array = asarray(["free_lodger", "owner"])
        >>> encoded_array = HousingOccupancyStatus.encode(string_identifier_array)
        >>> encoded_array[0]
        2  # Encoded value

        >>> free_lodger = HousingOccupancyStatus.free_lodger
        >>> owner = HousingOccupancyStatus.owner
        >>> enum_item_array = asarray([free_lodger, owner])
        >>> encoded_array = HousingOccupancyStatus.encode(enum_item_array)
        >>> encoded_array[0]
        2  # Encoded value
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
