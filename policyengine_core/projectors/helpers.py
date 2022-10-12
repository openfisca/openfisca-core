from openfisca_core import projectors


def projectable(function):
    """
    Decorator to indicate that when called on a projector, the outcome of the function must be projected.
    For instance person.household.sum(...) must be projected on person, while it would not make sense for person.household.get_holder.
    """
    function.projectable = True
    return function


def get_projector_from_shortcut(population, shortcut, parent = None):
    if population.entity.is_person:
        if shortcut in population.simulation.populations:
            entity_2 = population.simulation.populations[shortcut]
            return projectors.EntityToPersonProjector(entity_2, parent)
    else:
        if shortcut == 'first_person':
            return projectors.FirstPersonToEntityProjector(population, parent)
        role = next((role for role in population.entity.flattened_roles if (role.max == 1) and (role.key == shortcut)), None)
        if role:
            return projectors.UniqueRoleToEntityProjector(population, role, parent)
        if shortcut in population.entity.containing_entities:
            return getattr(projectors.FirstPersonToEntityProjector(population, parent), shortcut)
