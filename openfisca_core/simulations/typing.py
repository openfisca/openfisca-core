from __future__ import annotations

import typing
from collections.abc import Sequence
from numpy.typing import NDArray as Array
from typing import Any, Iterable, Protocol, TypedDict, Union
from typing_extensions import TypeAlias

import numpy

AbbrParams: TypeAlias = dict[str, dict[str, object]]

FullParams: TypeAlias = dict[str, dict[str, AbbrParams]]

AxesParams: TypeAlias = dict[str, list[list["AxisParams"]]]

EntsParams: TypeAlias = dict[str, Union[str, list[str]]]

ImplParams: TypeAlias = Union[EntsParams, FullParams, AxesParams]

ExplParams: TypeAlias = Union[dict[str, EntsParams], FullParams, AxesParams]

NoAxParams: TypeAlias = Union[dict[str, EntsParams], FullParams]

Params: TypeAlias = Union[dict[str, EntsParams], FullParams, AxesParams, AbbrParams]


class AxisParams(TypedDict, total=False):
    name: str
    count: int
    min: float
    max: float
    period: str | int
    index: int


class Entity(Protocol):
    key: str
    plural: str | None

    @typing.overload
    def get_variable(
        self,
        variable_name: str,
        check_existence: bool = True,
    ) -> Variable:
        ...

    @typing.overload
    def get_variable(
        self,
        variable_name: str,
        check_existence: bool = False,
    ) -> Variable | None:
        ...

    def get_variable(
        self,
        variable_name: str,
        check_existence: bool = ...,
    ) -> Variable | None:
        ...


class SingleEntity(Entity):
    ...


class GroupEntity(Entity):
    flattened_roles: Iterable[Role]


class Holder(Protocol):
    variable: Variable

    def set_input(
        self,
        period: Period,
        array: Array[Any] | Sequence[object],
    ) -> Array[Any] | None:
        ...


class Period(Protocol):
    ...


class Role(Protocol):
    ...


class Population(Protocol):
    count: int
    entity: Entity
    ids: Array[numpy.str_]

    def get_holder(self, variable_name: str) -> Holder:
        ...


class SinglePopulation(Population):
    ...


class GroupPopulation(Population):
    def nb_persons(self, role: Role | None = ...) -> int:
        ...


class TaxBenefitSystem(Protocol):
    person_entity: SingleEntity
    variables: dict[str, Variable]

    def entities_by_singular(self) -> Iterable[str]:
        ...

    def entities_plural(self) -> Iterable[str]:
        ...

    def instantiate_entities(
        self,
    ) -> dict[str, Union[SinglePopulation, GroupPopulation]]:
        ...


class Variable(Protocol):
    end: str

    def default_array(self, array_size: int) -> Array[Any]:
        ...
