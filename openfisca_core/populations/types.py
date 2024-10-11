from __future__ import annotations

from collections.abc import Iterable, MutableMapping
from typing import Union
from typing_extensions import NewType, TypeAlias

from openfisca_core.types import (
    Array,
    CoreEntity,
    CorePopulation,
    DTypeLike,
    EntityKey,
    GroupEntity,
    Holder,
    Period,
    PeriodStr,
    Simulation,
    SingleEntity,
    SinglePopulation,
    VariableName,
)

from numpy import (
    bool_ as BoolDType,
    float32 as FloatDType,
    generic as VarDType,
    str_ as StrDType,
)

# Commons

#: Type alias for an array of strings.
StrArray: TypeAlias = Array[StrDType]

#: Type alias for an array of booleans.
BoolArray: TypeAlias = Array[BoolDType]

#: Type alias for an array of floats.
FloatArray: TypeAlias = Array[FloatDType]

# Periods

#: New type for a period integer.
PeriodInt = NewType("PeriodInt", int)

#: Type alias for a period-like object.
PeriodLike: TypeAlias = Union[Period, PeriodStr, PeriodInt]

# Populations

#: Type alias for a population's holders.
Holders: TypeAlias = MutableMapping[VariableName, Holder]

# TODO(Mauko Quiroga-Alvarado): I'm not sure if this type alias is correct.
# https://openfisca.org/doc/coding-the-legislation/50_entities.html
Members: TypeAlias = Iterable[SinglePopulation]


__all__ = [
    "CoreEntity",
    "CorePopulation",
    "DTypeLike",
    "EntityKey",
    "GroupEntity",
    "Holder",
    "Period",
    "Simulation",
    "SingleEntity",
    "SinglePopulation",
    "VarDType",
    "VariableName",
]
