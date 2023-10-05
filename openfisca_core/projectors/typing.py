from __future__ import annotations

from collections.abc import Mapping
from typing import Iterable, Protocol


class Entity(Protocol):
    @property
    def is_person(self) -> bool:
        ...


class GroupEntity(Protocol):
    @property
    def containing_entities(self) -> Iterable[str]:
        ...

    @property
    def is_person(self) -> bool:
        ...

    @property
    def flattened_roles(self) -> Iterable[Role]:
        ...


class Role(Protocol):
    ...


class Population(Protocol):
    @property
    def entity(self) -> Entity | GroupEntity:
        ...

    @property
    def simulation(self) -> Simulation:
        ...


class GroupPopulation(Protocol):
    @property
    def entity(self) -> Entity | GroupEntity:
        ...

    @property
    def simulation(self) -> Simulation:
        ...


class Simulation(Protocol):
    @property
    def populations(self) -> Mapping[str, Population | GroupPopulation]:
        ...
