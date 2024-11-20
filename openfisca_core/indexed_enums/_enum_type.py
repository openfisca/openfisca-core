from __future__ import annotations

from typing import final

import numpy

from . import types as t


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

        >>> Housing.indices
        array([0, 1], dtype=uint8)

        >>> Housing.names
        array(['OWNER', 'TENANT'], dtype='<U6')

        >>> Housing.enums
        array([Housing.OWNER, Housing.TENANT], dtype=object)

    """

    def __new__(
        metacls,
        name: str,
        bases: tuple[type, ...],
        classdict: t.EnumDict,
        **kwds: object,
    ) -> t.EnumType:
        """Create a new indexed enum class."""
        # Create the enum class.
        cls = super().__new__(metacls, name, bases, classdict, **kwds)

        # If the enum class has no members, return it as is.
        if not cls.__members__:
            return cls

        # Add the indices attribute to the enum class.
        cls.indices = numpy.arange(len(cls), dtype=t.EnumDType)

        # Add the names attribute to the enum class.
        cls.names = numpy.array(cls._member_names_, dtype=t.StrDType)

        # Add the enums attribute to the enum class.
        cls.enums = numpy.array(cls, dtype=t.ObjDType)

        # Return the modified enum class.
        return cls

    def __dir__(cls) -> list[str]:
        return sorted({"indices", "names", "enums", *super().__dir__()})

    def __hash__(cls) -> int:
        return object.__hash__(cls.__name__)

    def __eq__(cls, other: object) -> bool:
        return hash(cls) == hash(other)

    def __ne__(cls, other: object) -> bool:
        return hash(cls) != hash(other)


__all__ = ["EnumType"]
