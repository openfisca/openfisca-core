from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from openfisca_core.types import Entity


class Population(Protocol):
    @property
    def entity(self) -> Entity: ...

    @property
    def simulation(self) -> Simulation: ...


class GroupPopulation(Protocol):
    @property
    def entity(self) -> Entity: ...

    @property
    def simulation(self) -> Simulation: ...


class Simulation(Protocol):
    @property
    def populations(self) -> Mapping[str, Population | GroupPopulation]: ...
