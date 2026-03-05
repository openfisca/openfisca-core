"""This module contains the _BuildDefaultSimulation class."""

from __future__ import annotations

from typing import Union
from typing_extensions import Self

import numpy

from .simulation import Simulation
from .typing import Entity, Population, TaxBenefitSystem


class _BuildDefaultSimulation:
    """Build a default simulation.

    Args:
        tax_benefit_system(TaxBenefitSystem): The tax-benefit system.
        count(int): The number of persons (and, by default, of each group entity).
        group_members: Optional mapping from group entity key to a 1D array of
            group entity id per person (length ``count``). When provided, that
            group's ``members_entity_id`` and ``count`` are set from the array
            instead of the default (one person per group). Use this when tests
            or examples need a specific grouping (e.g. 4 persons in 2 households).

    Examples:
        >>> from openfisca_core import entities, taxbenefitsystems

        >>> role = {"key": "stray", "plural": "stray", "label": "", "doc": ""}
        >>> single_entity = entities.Entity("dog", "dogs", "", "")
        >>> group_entity = entities.GroupEntity("pack", "packs", "", "", [role])
        >>> test_entities = [single_entity, group_entity]
        >>> tax_benefit_system = taxbenefitsystems.TaxBenefitSystem(test_entities)
        >>> count = 1
        >>> builder = (
        ...     _BuildDefaultSimulation(tax_benefit_system, count)
        ...     .add_count()
        ...     .add_ids()
        ...     .add_members_entity_id()
        ...     .add_id_to_rownum()
        ... )

        >>> builder.count
        1

        >>> sorted(builder.populations.keys())
        ['dog', 'pack']

        >>> sorted(builder.simulation.populations.keys())
        ['dog', 'pack']

    """

    #: The number of Population.
    count: int

    #: Optional per-group entity key -> array of group id per person.
    group_members: dict[str, numpy.ndarray] | None

    #: The built populations.
    populations: dict[str, Union[Population[Entity]]]

    #: The built simulation.
    simulation: Simulation

    def __init__(
        self,
        tax_benefit_system: TaxBenefitSystem,
        count: int,
        group_members: Mapping[str, NDArray[Any]] | None = None,
    ) -> None:
        self.count = count
        self.group_members = group_members
        self.populations = tax_benefit_system.instantiate_entities()
        self.simulation = Simulation(tax_benefit_system, self.populations)

    def add_count(self) -> Self:
        """Add the number of Population to the simulation.

        Returns:
            _BuildDefaultSimulation: The builder.

        Examples:
            >>> from openfisca_core import entities, taxbenefitsystems

            >>> role = {"key": "stray", "plural": "stray", "label": "", "doc": ""}
            >>> single_entity = entities.Entity("dog", "dogs", "", "")
            >>> group_entity = entities.GroupEntity("pack", "packs", "", "", [role])
            >>> test_entities = [single_entity, group_entity]
            >>> tax_benefit_system = taxbenefitsystems.TaxBenefitSystem(test_entities)
            >>> count = 2
            >>> builder = _BuildDefaultSimulation(tax_benefit_system, count)

            >>> builder.add_count()
            <..._BuildDefaultSimulation object at ...>

            >>> builder.populations["dog"].count
            2

            >>> builder.populations["pack"].count
            2

        """
        for population in self.populations.values():
            population.count = self.count

        return self

    def add_ids(self) -> Self:
        """Add the populations ids to the simulation.

        Returns:
            _BuildDefaultSimulation: The builder.

        Examples:
            >>> from openfisca_core import entities, taxbenefitsystems

            >>> role = {"key": "stray", "plural": "stray", "label": "", "doc": ""}
            >>> single_entity = entities.Entity("dog", "dogs", "", "")
            >>> group_entity = entities.GroupEntity("pack", "packs", "", "", [role])
            >>> test_entities = [single_entity, group_entity]
            >>> tax_benefit_system = taxbenefitsystems.TaxBenefitSystem(test_entities)
            >>> count = 2
            >>> builder = _BuildDefaultSimulation(tax_benefit_system, count)

            >>> builder.add_ids()
            <..._BuildDefaultSimulation object at ...>

            >>> builder.populations["dog"].ids
            array([0, 1])

            >>> builder.populations["pack"].ids
            array([0, 1])

        """
        for population in self.populations.values():
            population.ids = numpy.array(range(self.count))

        return self

    def add_id_to_rownum(self) -> Self:
        """Set identity id_to_rownum mapping on all populations.

        For static simulations, each entity's permanent ID equals its row
        position, so id_to_rownum is the identity: id_to_rownum[i] = i.
        """
        for population in self.populations.values():
            population._id_to_rownum = numpy.arange(self.count, dtype=numpy.intp)
        return self

    def add_members_entity_id(self) -> Self:
        """Set group populations' members_entity_id (and count when using group_members).

        Default: each person in their own group (members_entity_id = 0..count-1).
        When ``group_members`` was passed to the builder, each listed group uses
        the given array and its count is derived from it (clearing internal caches).

        Returns:
            _BuildDefaultSimulation: The builder.

        Examples:
            >>> from openfisca_core import entities, taxbenefitsystems

            >>> role = {"key": "stray", "plural": "stray", "label": "", "doc": ""}
            >>> single_entity = entities.Entity("dog", "dogs", "", "")
            >>> group_entity = entities.GroupEntity("pack", "packs", "", "", [role])
            >>> test_entities = [single_entity, group_entity]
            >>> tax_benefit_system = taxbenefitsystems.TaxBenefitSystem(test_entities)
            >>> count = 2
            >>> builder = _BuildDefaultSimulation(tax_benefit_system, count)

            >>> builder.add_members_entity_id()
            <..._BuildDefaultSimulation object at ...>

            >>> population = builder.populations["pack"]

            >>> hasattr(population, "members_entity_id")
            True

            >>> population.members_entity_id
            array([0, 1])

        """
        for population in self.populations.values():
            if not hasattr(population, "members_entity_id"):
                continue
            key = population.entity.key
            if self.group_members and key in self.group_members:
                arr = numpy.asarray(self.group_members[key], dtype=numpy.int32)
                if hasattr(population, "set_members_entity_id"):
                    population.set_members_entity_id(arr)
                else:
                    population.members_entity_id = arr
                    population.count = int(numpy.max(arr)) + 1
                    population._members_position = None
                    population._ordered_members_map = None
            else:
                population.members_entity_id = numpy.array(range(self.count))

        return self
