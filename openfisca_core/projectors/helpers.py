from __future__ import annotations

from collections.abc import Mapping

from openfisca_core import entities, projectors

from .typing import Entity, GroupEntity, GroupPopulation, Population, Role, Simulation


def projectable(function):
    """
    Decorator to indicate that when called on a projector, the outcome of the function must be projected.
    For instance person.household.sum(...) must be projected on person, while it would not make sense for person.household.get_holder.
    """
    function.projectable = True
    return function


def get_projector_from_shortcut(
    population: Population | GroupPopulation,
    shortcut: str,
    parent: projectors.Projector | None = None,
) -> projectors.Projector | None:
    """???.

        Args:
            population: ???
            shortcut: ???
            parent: ???

    Examples:
        >>> from openfisca_core import (
        ...     entities,
        ...     populations,
        ...     simulations,
        ...     taxbenefitsystems,
        ... )

        >>> entity_1 = entities.Entity("person", "", "", "")

        >>> entity_2 = entities.Entity("martian", "", "", "")

        >>> group_entity_1 = entities.GroupEntity("family", "", "", "", [])

        >>> roles = [
        ...     {"key": "person", "max": 1},
        ...     {"key": "martian", "subroles": ["cat", "dog"]},
        ... ]

        >>> group_entity_2 = entities.GroupEntity("household", "", "", "", roles)

        >>> population = populations.Population(entity_1)

        >>> group_population_1 = populations.GroupPopulation(entity_2, [])

        >>> group_population_2 = populations.GroupPopulation(group_entity_1, [])

        >>> group_population_3 = populations.GroupPopulation(group_entity_2, [])

        >>> populations = {
        ...     entity_1.key: population,
        ...     entity_2.key: group_population_1,
        ...     group_entity_1.key: group_population_2,
        ...     group_entity_2.key: group_population_3,
        ... }

        >>> tax_benefit_system = taxbenefitsystems.TaxBenefitSystem(
        ...     [entity_1, entity_2, group_entity_1, group_entity_2]
        ... )

        >>> simulation = simulations.Simulation(tax_benefit_system, populations)

        >>> get_projector_from_shortcut(population, "person")
        <...EntityToPersonProjector object at ...>

        >>> get_projector_from_shortcut(population, "martian")
        <...EntityToPersonProjector object at ...>

        >>> get_projector_from_shortcut(population, "family")
        <...EntityToPersonProjector object at ...>

        >>> get_projector_from_shortcut(population, "household")
        <...EntityToPersonProjector object at ...>

        >>> get_projector_from_shortcut(group_population_1, "person")
        <...EntityToPersonProjector object at ...>

        >>> get_projector_from_shortcut(group_population_1, "martian")
        <...EntityToPersonProjector object at ...>

        >>> get_projector_from_shortcut(group_population_1, "family")
        <...EntityToPersonProjector object at ...>

        >>> get_projector_from_shortcut(group_population_1, "household")
        <...EntityToPersonProjector object at ...>

        >>> get_projector_from_shortcut(group_population_2, "first_person")
        <...FirstPersonToEntityProjector object at ...>

        >>> get_projector_from_shortcut(group_population_3, "first_person")
        <...FirstPersonToEntityProjector object at ...>

        >>> get_projector_from_shortcut(group_population_3, "person")
        <...UniqueRoleToEntityProjector object at ...>

        >>> get_projector_from_shortcut(group_population_3, "cat")
        <...UniqueRoleToEntityProjector object at ...>

        >>> get_projector_from_shortcut(group_population_3, "dog")
        <...UniqueRoleToEntityProjector object at ...>

    """

    entity: Entity | GroupEntity = population.entity

    if isinstance(entity, entities.Entity) and entity.is_person:
        populations: Mapping[
            str, Population | GroupPopulation
        ] = population.simulation.populations

        if shortcut not in populations.keys():
            return None

        return projectors.EntityToPersonProjector(populations[shortcut], parent)

    if shortcut == "first_person":
        return projectors.FirstPersonToEntityProjector(population, parent)

    if isinstance(entity, entities.GroupEntity):
        role: Role | None = entities.find_role(entity, shortcut, total=1)

        if role is not None:
            return projectors.UniqueRoleToEntityProjector(population, role, parent)

        if shortcut in entity.containing_entities:
            projector: projectors.Projector = getattr(
                projectors.FirstPersonToEntityProjector(population, parent), shortcut
            )
            return projector

    return None
