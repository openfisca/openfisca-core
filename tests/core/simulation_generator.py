import numpy as np

import random
from openfisca_core.simulations import Simulation
from openfisca_core.periods import period as make_period


def make_simulation(tax_benefit_system, nb_persons, nb_groups, **kwargs):
    """
        Generate a simulation containing nb_persons persons spread in nb_groups groups
    """
    simulation = Simulation(tax_benefit_system = tax_benefit_system, **kwargs)
    simulation.persons.ids = np.arange(nb_persons)
    simulation.persons.count = nb_persons
    adults = [0] + sorted(random.sample(xrange(1, nb_persons), nb_groups - 1))

    members_entity_id = np.empty(nb_persons, dtype = int)
    members_legacy_role = np.empty(nb_persons, dtype = int)

    id_group = -1
    for id_person in range(nb_persons):
        if id_person in adults:
            id_group += 1
            legacy_role = 0
        else:
            legacy_role = 2 if legacy_role == 0 else legacy_role + 1
        members_legacy_role[id_person] = legacy_role
        members_entity_id[id_person] = id_group

    for entity in simulation.entities.itervalues():
        if not entity.is_person:
            entity.members_entity_id = members_entity_id
            entity.members_legacy_role = members_legacy_role
            entity.count = nb_groups
            entity.members_role = np.where(members_legacy_role == 0, entity.flattened_roles[0], entity.flattened_roles[-1])
    return simulation


def randomly_init_variable(simulation, variable_name, period, max_value, condition = None):
    """
        Initialise a variable with random values (from 0 to max_value) for the given period.
        If a condition vector is provided, only set the value of persons or groups for which condition is True
    """
    if condition is None:
        condition = True
    variable = simulation.tax_benefit_system.get_variable(variable_name)
    entity = simulation.get_variable_entity(variable_name)
    value = (np.random.rand(entity.count) * max_value * condition).astype(variable.dtype)
    entity.get_holder(variable_name).set_input(make_period(period), value)
