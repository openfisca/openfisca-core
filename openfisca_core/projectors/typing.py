from __future__ import annotations

from collections.abc import Mapping
from openfisca_core.entities.typing import Entity, GroupEntity, Role
from typing import Iterable, Protocol


class Population(Protocol):
    @property
    def entity(self) -> Entity:
        ...

    @property
    def simulation(self) -> Simulation:
        ...


class GroupPopulation(Protocol):
    @property
    def entity(self) -> GroupEntity:
        ...

    @property
    def simulation(self) -> Simulation:
        ...


class Simulation(Protocol):
    @property
    def populations(self) -> Mapping[str, Population | GroupPopulation]:
        ...
