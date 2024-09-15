"""Type aliases of OpenFisca models to use in the context of simulations."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Protocol, TypeVar, TypedDict, Union
from typing_extensions import NotRequired, Required, TypeAlias

from openfisca_core.types import Array
from openfisca_core.types import Failure as FailureType
from openfisca_core.types import Period as PeriodType
from openfisca_core.types import Success as SuccessType
from openfisca_core.types import Variable as VariableType

import datetime
from abc import abstractmethod

from numpy import bool_ as Bool
from numpy import datetime64 as Date
from numpy import float32 as Float
from numpy import int16 as Enum
from numpy import int32 as Int
from numpy import str_ as String

# Generic type variables.
E = TypeVar("E")
G = TypeVar("G", covariant=True)
U = TypeVar("U", bool, datetime.date, float, str)
V = TypeVar("V", covariant=True)

#: Type variable representing an error.
F = TypeVar("F", covariant=True)

#: Type variable representing a value.
A = TypeVar("A", covariant=True)

#: Type alias for numpy arrays values.
Item: TypeAlias = Union[Bool, Date, Enum, Float, Int, String]


# Commons


class Failure(FailureType[F], Protocol[F]):
    ...


class Success(SuccessType[A], Protocol[A]):
    ...


# Entities


#: Type alias for a simulation dictionary defining the roles.
Roles: TypeAlias = dict[str, Union[str, Iterable[str]]]


class Entity(Protocol):
    key: str
    plural: str | None

    def get_variable(
        self,
        __variable_name: str,
        __check_existence: bool = ...,
    ) -> Variable | None:
        ...


class SingleEntity(Entity, Protocol):
    ...


class GroupEntity(Entity, Protocol):
    @property
    @abstractmethod
    def flattened_roles(self) -> Iterable[Role[G]]:
        ...


class Role(Protocol[G]):
    ...


# Holders


class Holder(Protocol[V]):
    @property
    @abstractmethod
    def variable(self) -> Variable:
        ...

    def get_array(self, __period: str) -> Array[Item] | None:
        ...

    def set_input(
        self,
        __period: Period,
        __array: Array[Item] | Sequence[U],
    ) -> Array[Item] | None:
        ...


# Periods


class Period(PeriodType, Protocol):
    ...


# Populations


class Population(Protocol[E]):
    count: int
    entity: E
    ids: Array[String]

    def get_holder(self, __variable_name: str) -> Holder[V]:
        ...


class SinglePopulation(Population[E], Protocol):
    ...


class GroupPopulation(Population[E], Protocol):
    members_entity_id: Array[String]

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


class TaxBenefitSystem(Protocol):
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
    ) -> dict[str, Population[E]]:
        ...


# Variables


class Variable(VariableType, Protocol):
    definition_period: str
    end: str
    name: str

    def default_array(self, __array_size: int) -> Array[Item]:
        ...
