from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from openfisca_core import types as t

# Entities


class SingleEntity(t.SingleEntity, Protocol):
    ...


class GroupEntity(t.GroupEntity, Protocol):
    ...


class Role(t.Role, Protocol):
    ...


# Populations


class SinglePopulation(t.SinglePopulation, Protocol):
    @property
    def entity(self) -> t.SingleEntity:
        ...

    @property
    def simulation(self) -> Simulation:
        ...


class GroupPopulation(t.GroupPopulation, Protocol):
    @property
    def entity(self) -> t.GroupEntity:
        ...

    @property
    def simulation(self) -> Simulation:
        ...


# Simulations


class Simulation(t.Simulation, Protocol):
    @property
    def populations(self) -> Mapping[str, SinglePopulation | GroupPopulation]:
        ...
