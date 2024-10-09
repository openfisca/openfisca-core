from __future__ import annotations

from typing import final

import numpy

from . import types as t


def _item_list(enum_class: t.EnumType) -> t.ItemList:
    """Return the non-vectorised list of enum items."""
    return [  # type: ignore[var-annotated]
        (index, name, value)
        for index, (name, value) in enumerate(enum_class.__members__.items())
    ]


def _item_dtype(enum_class: t.EnumType) -> t.RecDType:
    """Return the dtype of the indexed enum's items."""
    size = max(map(len, enum_class.__members__.keys()))
    return numpy.dtype(
        (
            numpy.generic,
            {
                "index": (t.EnumDType, 0),
                "name": (f"U{size}", 2),
                "enum": (enum_class, 2 + size * 4),
            },
        )
    )


def _item_array(enum_class: t.EnumType) -> t.RecArray:
    """Return the indexed enum's items."""
    items = _item_list(enum_class)
    dtype = _item_dtype(enum_class)
    array = numpy.array(items, dtype=dtype)
    return array.view(numpy.recarray)


@final
class EnumType(t.EnumType):
    """Meta class for creating an indexed :class:`.Enum`.

    Examples:
        >>> from openfisca_core import indexed_enums as enum

        >>> class Enum(enum.Enum, metaclass=enum.EnumType):
        ...     pass

        >>> Enum.items
        Traceback (most recent call last):
        AttributeError: ...

        >>> class Housing(Enum):
        ...     OWNER = "Owner"
        ...     TENANT = "Tenant"

        >>> Housing.items
        rec.array([(0, 'OWNER', Housing.OWNER), (1, 'TENANT', Housing.TENAN...)

        >>> Housing.indices
        array([0, 1], dtype=int16)

        >>> Housing.names
        array(['OWNER', 'TENANT'], dtype='<U6')

        >>> Housing.enums
        array([Housing.OWNER, Housing.TENANT], dtype=object)

    """

    #: The items of the indexed enum class.
    items: t.RecArray

    @property
    def indices(cls) -> t.IndexArray:
        """Return the indices of the indexed enum class."""
        indices: t.IndexArray = cls.items.index
        return indices

    @property
    def names(cls) -> t.StrArray:
        """Return the names of the indexed enum class."""
        names: t.StrArray = cls.items.name
        return names

    @property
    def enums(cls) -> t.ObjArray:
        """Return the members of the indexed enum class."""
        enums: t.ObjArray = cls.items.enum
        return enums

    def __new__(
        metacls,
        cls: str,
        bases: tuple[type, ...],
        classdict: t.EnumDict,
        **kwds: object,
    ) -> t.EnumType:
        """Create a new indexed enum class."""
        # Create the enum class.
        enum_class = super().__new__(metacls, cls, bases, classdict, **kwds)

        # If the enum class has no members, return it as is.
        if not enum_class.__members__:
            return enum_class

        # Add the items attribute to the enum class.
        enum_class.items = _item_array(enum_class)

        # Return the modified enum class.
        return enum_class

    def __dir__(cls) -> list[str]:
        return sorted({"items", "indices", "names", "enums", *super().__dir__()})


__all__ = ["EnumType"]
