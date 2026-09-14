from __future__ import annotations

from collections.abc import Mapping

from openfisca_core.types import Role, Entity

from openfisca_core import entities, projectors

from .typing import GroupPopulation, Population


def projectable(function):
    """Decorator to indicate that when called on a projector, the outcome of the function must be projected.
    For instance person.household.sum(...) must be projected on person, while it would not make sense for person.household.get_holder.
    """
    function.projectable = True
    return function


def get_projector_from_shortcut(
    population: Population | GroupPopulation,
    shortcut: str,
    parent: projectors.Projector | None = None,
) -> projectors.Projector | None:
    """Get a projector from a shortcut.

    Projectors are used to project an invidividual Population's or a
    collective GroupPopulation's on to other populations.

    The currently available cases are projecting:
    - from an individual to a group
    - from a group to an individual
    - from a group to an individual with a unique role

    For example, if there are two entities, person (Entity) and household
    (Entity), on which calculations can be run (Population and
    GroupPopulation respectively), and there is a Variable "rent" defined for
    the household entity, then `person.household("rent")` will assign a rent to
    every person within that household.

    Behind the scenes, this is done thanks to a Projector, and this function is
    used to find the appropriate one for each case. In the above example, the
    `shortcut` argument would be "household", and the `population` argument
    would be the Population linked to the "person" Entity in the context
    of a specific Simulation and TaxBenefitSystem.

    Args:
        population (Population | GroupPopulation): Where to project from.
        shortcut (str): Where to project to.
        parent: ???

    Examples:
        >>> from openfisca_core import (
        ...     entities,
        ...     populations,
        ...     simulations,
        ...     taxbenefitsystems,
        ... )

        >>> entity = entities.Entity("person", "", "", "")

        >>> group_entity_1 = entities.Entity("family", "", "", "")

        >>> group_entity_1.add_link(entity, [{"key": "person", "max": 1}])

        >>> roles = [
        ...     {"key": "person", "max": 1},
        ...     {"key": "animal", "subroles": ["cat", "dog"]},
        ... ]

        >>> group_entity_2 = entities.Entity("household", "", "", "")

        >>> group_entity_2.add_link(entity, roles)

        >>> population = populations.Population(entity)

        >>> group_population_1 = populations.GroupPopulation(group_entity_1, [])

        >>> group_population_2 = populations.GroupPopulation(group_entity_2, [])

        >>> populations = {
        ...     entity.key: population,
        ...     group_entity_1.key: group_population_1,
        ...     group_entity_2.key: group_population_2,
        ... }

        >>> tax_benefit_system = taxbenefitsystems.TaxBenefitSystem(
        ...     [entity, group_entity_1, group_entity_2]
        ... )

        >>> simulation = simulations.Simulation(tax_benefit_system, populations)

        >>> get_projector_from_shortcut(group_population_1, "person")
        <...UniqueRoleToEntityProjector object at ...>

        >>> get_projector_from_shortcut(population, "family")
        <...EntityToPersonProjector object at ...>

        >>> get_projector_from_shortcut(population, "household")
        <...EntityToPersonProjector object at ...>

        >>> get_projector_from_shortcut(group_population_2, "first_person")
        <...FirstPersonToEntityProjector object at ...>

        >>> get_projector_from_shortcut(group_population_2, "person")
        <...UniqueRoleToEntityProjector object at ...>

        >>> get_projector_from_shortcut(group_population_2, "cat")
        <...UniqueRoleToEntityProjector object at ...>

        >>> get_projector_from_shortcut(group_population_2, "dog")
        <...UniqueRoleToEntityProjector object at ...>

    """
    entity: Entity = population.entity

    if shortcut in [k.b.key for k in entity.links]:
        return projectors.EntityToPersonProjector(population.simulation.populations[shortcut], parent)

    if shortcut == "first_person":
        return projectors.FirstPersonToEntityProjector(population, parent)

    if isinstance(entity, entities.Entity):
        role: Role | None = entities.find_role(entity.flattened_roles, shortcut, total=1)

        if role is not None:
            return projectors.UniqueRoleToEntityProjector(population, role, parent)

    return None
