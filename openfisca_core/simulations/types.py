"""Type aliases of OpenFisca models to use in the context of simulations."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Protocol, TypeVar, TypedDict, Union
from typing_extensions import NotRequired, Required, TypeAlias

import datetime
from abc import abstractmethod

from numpy import bool_ as Bool
from numpy import datetime64 as Date
from numpy import float32 as Float
from numpy import int16 as Enum
from numpy import int32 as Int
from numpy import str_ as String

from openfisca_core import types as t

# Generic type variables.
D = TypeVar("D")
E = TypeVar("E", covariant=True)
G = TypeVar("G", covariant=True)
T = TypeVar("T", Bool, Date, Enum, Float, Int, String, covariant=True)
U = TypeVar("U", bool, datetime.date, float, str)
V = TypeVar("V", covariant=True)

#: Type alias for numpy arrays values.
Item: TypeAlias = Union[Bool, Date, Enum, Float, Int, String]


# Entities


#: Type alias for a simulation dictionary defining the roles.
Roles: TypeAlias = dict[str, Union[str, Iterable[str]]]


class CoreEntity(t.CoreEntity, Protocol):
    key: str
    plural: str | None

    def get_variable(
        self,
        __variable_name: str,
        __check_existence: bool = ...,
    ) -> Variable[T] | None:
        ...


class SingleEntity(t.SingleEntity, Protocol):
    ...


class GroupEntity(t.GroupEntity, Protocol):
    @property
    @abstractmethod
    def flattened_roles(self) -> Iterable[Role[G]]:
        ...


class Role(t.Role, Protocol[G]):
    ...


# Holders


class Holder(t.Holder, Protocol[V]):
    @property
    @abstractmethod
    def variable(self) -> Variable[T]:
        ...

    def get_array(self, __period: str) -> t.Array[T] | None:
        ...

    def set_input(
        self,
        __period: Period,
        __array: t.Array[T] | Sequence[U],
    ) -> t.Array[T] | None:
        ...


# Periods


class Period(t.Period, Protocol):
    ...


# Populations


class CorePopulation(t.CorePopulation, Protocol[D]):
    entity: D

    def get_holder(self, __variable_name: str) -> Holder[V]:
        ...


class SinglePopulation(t.SinglePopulation, Protocol[E]):
    ...


class GroupPopulation(t.GroupPopulation, Protocol[E]):
    members_entity_id: t.Array[String]

    def nb_persons(self, __role: Role[G] | None = ...) -> int:
        ...


# Simulations


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
    Variables, ImplicitGroupEntities, FullySpecifiedEntities
]

#: Type alias for a simulation dictionary with axes parameters.
ParamsWithAxes: TypeAlias = Union[Axes, ParamsWithoutAxes]

#: Type alias for a simulation dictionary with all the possible scenarios.
Params: TypeAlias = ParamsWithAxes


class Axis(TypedDict, total=False):
    count: Required[int]
    index: NotRequired[int]
    max: Required[float]
    min: Required[float]
    name: Required[str]
    period: NotRequired[str | int]


# Tax-Benefit systems


class TaxBenefitSystem(t.TaxBenefitSystem, Protocol):
    @property
    @abstractmethod
    def person_entity(self) -> SingleEntity:
        ...

    @person_entity.setter
    @abstractmethod
    def person_entity(self, person_entity: SingleEntity) -> None:
        ...

    @property
    @abstractmethod
    def variables(self) -> dict[str, V]:
        ...

    def entities_by_singular(self) -> dict[str, E]:
        ...

    def entities_plural(self) -> Iterable[str]:
        ...

    def get_variable(
        self,
        __variable_name: str,
        __check_existence: bool = ...,
    ) -> V | None:
        ...

    def instantiate_entities(
        self,
    ) -> dict[str, GroupPopulation[E]]:
        ...


# Variables


class Variable(t.Variable, Protocol[T]):
    definition_period: str
    end: str
    name: str

    def default_array(self, __array_size: int) -> t.Array[T]:
        ...
