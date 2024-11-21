"""Type aliases of OpenFisca models to use in the context of simulations."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar, TypedDict, Union
from typing_extensions import NotRequired, Required, TypeAlias

import datetime

#: Generic type variables.
E = TypeVar("E")
U = TypeVar("U", bool, datetime.date, float, str)


#: Type alias for a simulation dictionary defining the roles.
Roles: TypeAlias = dict[str, Union[str, Iterable[str]]]

#: Type alias for a simulation dictionary with undated variables.
UndatedVariable: TypeAlias = dict[str, object]

#: Type alias for a simulation dictionary with dated variables.
DatedVariable: TypeAlias = dict[str, UndatedVariable]

#: Type alias for a simulation dictionary with abbreviated entities.
Variables: TypeAlias = dict[str, Union[UndatedVariable, DatedVariable]]

#: Type alias for a simulation with fully specified single entities.
SingleEntities: TypeAlias = dict[str, dict[str, Variables]]

#: Type alias for a simulation dictionary with implicit group entities.
ImplicitGroupEntities: TypeAlias = dict[str, Union[Roles, Variables]]

#: Type alias for a simulation dictionary with explicit group entities.
GroupEntities: TypeAlias = dict[str, ImplicitGroupEntities]

#: Type alias for a simulation dictionary with fully specified entities.
FullySpecifiedEntities: TypeAlias = Union[SingleEntities, GroupEntities]

#: Type alias for a simulation dictionary with axes parameters.
Axes: TypeAlias = dict[str, Iterable[Iterable["Axis"]]]

#: Type alias for a simulation dictionary without axes parameters.
ParamsWithoutAxes: TypeAlias = Union[
    Variables,
    ImplicitGroupEntities,
    FullySpecifiedEntities,
]

#: Type alias for a simulation dictionary with axes parameters.
ParamsWithAxes: TypeAlias = Union[Axes, ParamsWithoutAxes]

#: Type alias for a simulation dictionary with all the possible scenarios.
Params: TypeAlias = ParamsWithAxes


class Axis(TypedDict, total=False):
    """Interface representing an axis of a simulation."""

    count: Required[int]
    index: NotRequired[int]
    max: Required[float]
    min: Required[float]
    name: Required[str]
    period: NotRequired[str | int]
