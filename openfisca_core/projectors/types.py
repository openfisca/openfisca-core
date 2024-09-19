from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from openfisca_core import types as t

# Entities


class CoreEntity(t.CoreEntity, Protocol):
    ...


class Role(t.Role, Protocol):
    ...


# Projectors


class Projector(Protocol):
    ...


# Populations


class CorePopulation(t.CorePopulation, Protocol):
    @property
    def entity(self) -> CoreEntity:
        ...

    @property
    def simulation(self) -> Simulation:
        ...


# Simulations


class Simulation(t.Simulation, Protocol):
    @property
    def populations(self) -> Mapping[str, CorePopulation]:
        ...
