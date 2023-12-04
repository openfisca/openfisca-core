from __future__ import annotations

from numpy.typing import NDArray as Array
from typing import Protocol, TypedDict


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
        check_existence: bool = False,
    ) -> Variable | None:
        ...


class Population(Protocol):
    ...


class Role(Protocol):
    ...


class Variable(Protocol):
    def default_array(self, array_size: int) -> Array:
        ...
