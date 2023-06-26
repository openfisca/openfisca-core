from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Mapping

    from openfisca_core.types import GroupEntity, SingleEntity


class Population(Protocol):
    @property
    def entity(self) -> SingleEntity: ...

    @property
    def simulation(self) -> Simulation: ...


class GroupPopulation(Protocol):
    @property
    def entity(self) -> GroupEntity: ...

    @property
    def simulation(self) -> Simulation: ...


class Simulation(Protocol):
    @property
    def populations(self) -> Mapping[str, Population | GroupPopulation]: ...
