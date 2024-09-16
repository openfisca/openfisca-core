"""Type aliases of OpenFisca models to use in the context of simulations."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Literal, NewType, Protocol, TypeVar, Union
from typing_extensions import NotRequired, TypeAlias, TypedDict

import datetime

from numpy import bool_ as Bool
from numpy import datetime64 as Date
from numpy import float32 as Float
from numpy import int16 as Enum
from numpy import int32 as Int
from numpy import str_ as String

from openfisca_core import types as t

# Generic type variables.
G = TypeVar("G", covariant=True)
T = TypeVar("T", Bool, Date, Enum, Float, Int, String, covariant=True)
U = TypeVar("U", bool, datetime.date, float, str)
V = TypeVar("V", covariant=True)

# New types.

#: Literally "axes".
AxesKey = Literal["axes"]

#: For example "Juan".
EntityId = NewType("EntityId", int)

#: For example "person".
EntityKey = NewType("EntityKey", str)

#: For example "persons".
EntityPlural = NewType("EntityPlural", str)

#: For example "2023-12".
PeriodStr = NewType("PeriodStr", str)

#: For example "principal".
RoleKey = NewType("RoleKey", str)

#: For example "parents".
RolePlural = NewType("RolePlural", str)

#: For example "salary".
VariableName = NewType("VariableName", str)

# Type aliases.

#: Type alias for numpy arrays values.
Item: TypeAlias = Union[Bool, Date, Enum, Float, Int, String]

#: Type Alias for a numpy Array.
Array: TypeAlias = t.Array

#: Type alias for a role identifier.
RoleId: TypeAlias = EntityId

# Entities


class CoreEntity(t.CoreEntity, Protocol):
    key: EntityKey
    plural: EntityPlural | None

    def get_variable(
        self,
        __variable_name: VariableName,
        check_existence: bool = ...,
    ) -> Variable[T] | None:
        ...


class SingleEntity(t.SingleEntity, Protocol):
    ...


class GroupEntity(t.GroupEntity, Protocol):
    @property
    def flattened_roles(self) -> Iterable[Role[G]]:
        ...


class Role(t.Role, Protocol[G]):
    ...


# Holders


class Holder(t.Holder, Protocol[V]):
    @property
    def variable(self) -> Variable[T]:
        ...

    def get_array(self, __period: PeriodStr) -> t.Array[T] | None:
        ...

    def set_input(
        self,
        __period: Period,
        __array: t.Array[T] | Sequence[U],
    ) -> t.Array[T] | None:
        ...


# Periods


class Instant(t.Instant, Protocol):
    ...


class Period(t.Period, Protocol):
    ...


# Populations


class CorePopulation(t.CorePopulation, Protocol):
    entity: CoreEntity

    def get_holder(self, __variable_name: VariableName) -> Holder[V]:
        ...


class SinglePopulation(t.SinglePopulation, Protocol):
    entity: SingleEntity


class GroupPopulation(t.GroupPopulation, Protocol):
    entity: GroupEntity
    members_entity_id: t.Array[String]

    def nb_persons(self, __role: Role[G] | None = ...) -> int:
        ...


# Simulations

#: Dictionary with axes parameters per variable.
InputBuffer: TypeAlias = dict[VariableName, dict[PeriodStr, Array]]

#: Dictionary with entity/population key/pairs.
Populations: TypeAlias = dict[EntityKey, GroupPopulation]

#: Dictionary with single entity count per group entity.
EntityCounts: TypeAlias = dict[EntityPlural, int]

#: Dictionary with a list of single entities per group entity.
EntityIds: TypeAlias = dict[EntityPlural, Iterable[EntityId]]

#: Dictionary with a list of members per group entity.
Memberships: TypeAlias = dict[EntityPlural, Iterable[int]]

#: Dictionary with a list of roles per group entity.
EntityRoles: TypeAlias = dict[EntityPlural, Iterable[RoleKey]]

#: Dictionary with a map between variables and entities.
VariableEntity: TypeAlias = dict[VariableName, CoreEntity]

#: Type alias for a simulation dictionary with undated variable values.
PureValue: TypeAlias = Union[object, Sequence[object]]

#: Type alias for a simulation dictionary with dated variable values.
DatedValue: TypeAlias = dict[PeriodStr, PureValue]

#: Type alias for a simulation dictionary with abbreviated entities.
Variables: TypeAlias = dict[VariableName, Union[PureValue, DatedValue]]

#: Type alias for a simulation dictionary defining the roles.
Roles: TypeAlias = Union[dict[RoleKey, RoleId], dict[RolePlural, Iterable[RoleId]]]

#: Type alias for a simulation dictionary with axes parameters.
Axes: TypeAlias = Iterable[Iterable["Axis"]]

#: Type alias for a simulation with fully specified single entities.
SingleEntities: TypeAlias = dict[str, dict[str, Variables]]

#: Type alias for a simulation dictionary with implicit group entities.
ImplicitGroupEntities: TypeAlias = dict[str, Union[Roles, Variables]]

#: Type alias for a simulation dictionary with explicit group entities.
GroupEntities: TypeAlias = dict[str, ImplicitGroupEntities]

#: Type alias for a simulation dictionary with fully specified entities.
FullySpecifiedEntities: TypeAlias = Union[SingleEntities, GroupEntities]

#: Type alias for a simulation dictionary without axes parameters.
ParamsWithoutAxes: TypeAlias = Union[
    Variables, ImplicitGroupEntities, FullySpecifiedEntities
]

#: Type alias for a simulation dictionary with axes parameters.
ParamsWithAxes: TypeAlias = Union[dict[AxesKey, Axes], ParamsWithoutAxes]

#: Type alias for a simulation dictionary with all the possible scenarios.
Params: TypeAlias = ParamsWithAxes


class Axis(TypedDict):
    count: int
    max: float
    min: float
    index: NotRequired[int]
    name: EntityKey
    period: NotRequired[Union[str, int]]


class Simulation(t.Simulation, Protocol):
    ...


# Tax-Benefit systems


class TaxBenefitSystem(t.TaxBenefitSystem, Protocol):
    @property
    def person_entity(self) -> SingleEntity:
        ...

    @person_entity.setter
    def person_entity(self, person_entity: SingleEntity) -> None:
        ...

    @property
    def variables(self) -> dict[str, V]:
        ...

    def entities_by_singular(self) -> dict[EntityKey, CoreEntity]:
        ...

    def entities_plural(self) -> Iterable[EntityPlural]:
        ...

    def get_variable(
        self,
        __variable_name: VariableName,
        check_existence: bool = ...,
    ) -> Variable[T] | None:
        ...

    def instantiate_entities(
        self,
    ) -> Populations:
        ...


# Variables


class Variable(t.Variable, Protocol[T]):
    calculate_output: Callable[[Simulation, str, str], t.Array[T]] | None
    definition_period: str
    end: str
    name: VariableName

    def default_array(self, __array_size: int) -> t.Array[T]:
        ...

    def get_formula(
        self, __period: Instant | Period | PeriodStr | Int
    ) -> Formula | None:
        ...


class Formula(t.Formula, Protocol):
    ...
