from __future__ import annotations

import abc
from numpy.typing import NDArray
from typing import Any, Protocol


class Formula3(Protocol):
    @abc.abstractmethod
    def __call__(
        self, __population: Population, __instant: Instant, __params: Params
    ) -> NDArray[Any]:
        ...


class Formula2(Protocol):
    @abc.abstractmethod
    def __call__(self, __population: Population, __instant: Instant) -> NDArray[Any]:
        ...


class Instant(Protocol):
    ...


class ParameterNodeAtInstant(Protocol):
    ...


class Params(Protocol):
    @abc.abstractmethod
    def __call__(self, __instant: Instant) -> ParameterNodeAtInstant:
        ...


class Population(Protocol):
    ...
