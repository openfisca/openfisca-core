"""Type aliases of OpenFisca models to use in the context of simulations."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from numpy.typing import NDArray as Array
from typing import Protocol, TypeVar, TypedDict, Union
from typing_extensions import NotRequired, Required, TypeAlias

import datetime
from abc import abstractmethod

from numpy import (
    bool_ as Bool,
    datetime64 as Date,
    float32 as Float,
    int16 as Enum,
    int32 as Int,
    str_ as String,
)

#: Generic type variables.
E = TypeVar("E")
G = TypeVar("G", covariant=True)
T = TypeVar("T", Bool, Date, Enum, Float, Int, String, covariant=True)
U = TypeVar("U", bool, datetime.date, float, str)
V = TypeVar("V", covariant=True)


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


class Entity(Protocol):
    """Interface representing an entity of a simulation."""

    key: str
    plural: str | None

    def get_variable(
        self,
        __variable_name: str,
        __check_existence: bool = ...,
    ) -> Variable[T] | None:
        """Get a variable."""


class SingleEntity(Entity, Protocol):
    """Interface representing a single entity of a simulation."""


class GroupEntity(Entity, Protocol):
    """Interface representing a group entity of a simulation."""

    @property
    @abstractmethod
    def flattened_roles(self) -> Iterable[Role[G]]:
        """Get the flattened roles of the GroupEntity."""


class Holder(Protocol[V]):
    """Interface representing a holder of a simulation's computed values."""

    @property
    @abstractmethod
    def variable(self) -> Variable[T]:
        """Get the Variable of the Holder."""

    def get_array(self, __period: str) -> Array[T] | None:
        """Get the values of the Variable for a given Period."""

    def set_input(
        self,
        __period: Period,
        __array: Array[T] | Sequence[U],
    ) -> Array[T] | None:
        """Set values for a Variable for a given Period."""


class Period(Protocol):
    """Interface representing a period of a simulation."""


class Population(Protocol[E]):
    """Interface representing a data vector of an Entity."""

    count: int
    entity: E
    ids: Array[String]

    def get_holder(self, __variable_name: str) -> Holder[V]:
        """Get the holder of a Variable."""


class SinglePopulation(Population[E], Protocol):
    """Interface representing a data vector of a SingleEntity."""


class GroupPopulation(Population[E], Protocol):
    """Interface representing a data vector of a GroupEntity."""

    members_entity_id: Array[String]

    def nb_persons(self, __role: Role[G] | None = ...) -> int:
        """Get the number of persons for a given Role."""


class Role(Protocol[G]):
    """Interface representing a role of the group entities of a simulation."""


class TaxBenefitSystem(Protocol):
    """Interface representing a tax-benefit system."""

    @property
    @abstractmethod
    def person_entity(self) -> SingleEntity:
        """Get the person entity of the tax-benefit system."""

    @person_entity.setter
    @abstractmethod
    def person_entity(self, person_entity: SingleEntity) -> None:
        """Set the person entity of the tax-benefit system."""

    @property
    @abstractmethod
    def variables(self) -> dict[str, V]:
        """Get the variables of the tax-benefit system."""

    def entities_by_singular(self) -> dict[str, E]:
        """Get the singular form of the entities' keys."""

    def entities_plural(self) -> Iterable[str]:
        """Get the plural form of the entities' keys."""

    def get_variable(
        self,
        __variable_name: str,
        __check_existence: bool = ...,
    ) -> V | None:
        """Get a variable."""

    def instantiate_entities(
        self,
    ) -> dict[str, Population[E]]:
        """Instantiate the populations of each Entity."""


class Variable(Protocol[T]):
    """Interface representing a variable of a tax-benefit system."""

    end: str

    def default_array(self, __array_size: int) -> Array[T]:
        """Fill an array with the default value of the Variable."""
