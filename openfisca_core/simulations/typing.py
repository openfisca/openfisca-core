from __future__ import annotations

from numpy.typing import NDArray as Array
from typing import Any, Protocol, TypedDict
from collections.abc import Sequence


class AxisParams(TypedDict, total=False):
    name: str
    count: int
    min: float
    max: float
    period: str | int
    index: int


class Entity(Protocol):
    plural: str | None

    def get_variable(
        self,
        variable_name: str,
        check_existence: bool = ...,
    ) -> Variable | None:
        ...


class Holder(Protocol):
    variable: Variable
    def set_input(
        self,
        period: Period,
        array: Array[Any] | Sequence[Any],
    ) -> Array[Any] | None:
        ...


class Period(Protocol):
    ...


class Population(Protocol):
    count: int
    entity: Entity

    def get_holder(self, variable_name: str) -> Holder:
        ...


class Role(Protocol):
    ...


class GroupPopulation(Population):
    def nb_persons(self, role: Role | None = ...) -> int:
        ...


class TaxBenefitSystem(Protocol):
    ...


class Variable(Protocol):
    end: str

    def default_array(self, array_size: int) -> Array[Any]:
        ...
