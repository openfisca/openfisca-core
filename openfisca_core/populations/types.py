from __future__ import annotations

import enum
from collections.abc import Iterable, MutableMapping, Sequence
from typing import NamedTuple, TypeAlias

import strenum
from numpy import (
    bool_ as BoolDType,
)
from numpy import (
    float32 as FloatDType,
)
from numpy import (
    generic as VarDType,
)
from numpy import (
    int32 as IntDType,
)
from numpy import (
    str_ as StrDType,
)
from typing_extensions import TypedDict

from openfisca_core.types import (
    Array,
    CoreEntity,
    CorePopulation,
    DTypeLike,
    EntityKey,
    GroupEntity,
    Holder,
    MemoryUsage,
    Period,
    PeriodInt,
    PeriodStr,
    Role,
    Simulation,
    SingleEntity,
    SinglePopulation,
    VariableName,
)

# Commons

#: Type alias for an array of strings.
IntArray: TypeAlias = Array[IntDType]

#: Type alias for an array of strings.
StrArray: TypeAlias = Array[StrDType]

#: Type alias for an array of booleans.
BoolArray: TypeAlias = Array[BoolDType]

#: Type alias for an array of floats.
FloatArray: TypeAlias = Array[FloatDType]

#: Type alias for an array of generic objects.
VarArray: TypeAlias = Array[VarDType]

# Periods

#: Type alias for a period-like object.
PeriodLike: TypeAlias = Period | PeriodStr | PeriodInt

# Populations

#: Type alias for a population's holders.
HolderByVariable: TypeAlias = MutableMapping[VariableName, Holder]

# TODO(Mauko Quiroga-Alvarado): I'm not sure if this type alias is correct.
# https://openfisca.org/doc/coding-the-legislation/50_entities.html
Members: TypeAlias = Iterable[SinglePopulation]


class Option(strenum.StrEnum):
    ADD = enum.auto()
    DIVIDE = enum.auto()

    def __contains__(self, option: str) -> bool:
        return option.upper() is self


class Calculate(NamedTuple):
    variable: VariableName
    period: Period
    option: None | Sequence[Option]


class MemoryUsageByVariable(TypedDict, total=False):
    by_variable: dict[VariableName, MemoryUsage]
    total_nb_bytes: int


__all__ = [
    "CoreEntity",
    "CorePopulation",
    "DTypeLike",
    "EntityKey",
    "GroupEntity",
    "Holder",
    "MemoryUsage",
    "Period",
    "Role",
    "Simulation",
    "SingleEntity",
    "SinglePopulation",
    "VarDType",
    "VariableName",
]
