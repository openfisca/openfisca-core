"""This module contains the _BuildDefaultSimulation class."""

from typing import Union
from typing_extensions import Self

import numpy

from .simulation import Simulation
from .typing import Entity, Population, TaxBenefitSystem


class _BuildDefaultSimulation:
    """Build a default simulation.

    Args:
        tax_benefit_system(TaxBenefitSystem): The tax-benefit system.
        count(int): The number of periods.

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

    #: The built populations.
    populations: dict[str, Union[Population[Entity]]]

    #: The built simulation.
    simulation: Simulation

    def __init__(self, tax_benefit_system: TaxBenefitSystem, count: int) -> None:
        self.count = count
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

    def add_members_entity_id(self) -> Self:
        """Add ???

        Each SingleEntity has its own GroupEntity.

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
            if hasattr(population, "members_entity_id"):
                population.members_entity_id = numpy.array(range(self.count))

        return self
