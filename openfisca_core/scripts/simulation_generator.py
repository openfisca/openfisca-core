import numpy as np

import random
from openfisca_core.simulations import Simulation


def make_simulation(tax_benefit_system, nb_persons, nb_groups, **kwargs):
    """
        Generate a simulation containing nb_persons persons spread in nb_groups groups.

        Example:

        >>> from openfisca_core.scripts.simulation_generator import make_simulation
        >>> from openfisca_france import CountryTaxBenefitSystem
        >>> tbs = CountryTaxBenefitSystem()
        >>> simulation = make_simulation(tbs, 400, 100)  # Create a simulation with 400 persons, spread among 100 families
        >>> simulation.calculate('revenu_disponible', 2017)
    """
    simulation = Simulation(tax_benefit_system = tax_benefit_system, **kwargs)
    simulation.persons.ids = np.arange(nb_persons)
    simulation.persons.count = nb_persons
    adults = [0] + sorted(random.sample(range(1, nb_persons), nb_groups - 1))

    members_entity_id = np.empty(nb_persons, dtype = int)

    # A legacy role is an index that every person within an entity has. For instance, the 'demandeur' has legacy role 0, the 'conjoint' 1, the first 'child' 2, the second 3, etc.
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

    for entity in simulation.populations.values():
        if not entity.is_person:
            entity.members_entity_id = members_entity_id
            entity.count = nb_groups
            entity.members_role = np.where(members_legacy_role == 0, entity.flattened_roles[0], entity.flattened_roles[-1])
    return simulation


def randomly_init_variable(simulation, variable_name: str, period, max_value, condition = None):
    """
        Initialise a variable with random values (from 0 to max_value) for the given period.
        If a condition vector is provided, only set the value of persons or groups for which condition is True.

        Example:

        >>> from openfisca_core.scripts.simulation_generator import make_simulation, randomly_init_variable
        >>> from openfisca_france import CountryTaxBenefitSystem
        >>> tbs = CountryTaxBenefitSystem()
        >>> simulation = make_simulation(tbs, 400, 100)  # Create a simulation with 400 persons, spread among 100 families
        >>> randomly_init_variable(simulation, 'salaire_net', 2017, max_value = 50000, condition = simulation.persons.has_role(simulation.famille.DEMANDEUR))  # Randomly set a salaire_net for all persons between 0 and 50000?
        >>> simulation.calculate('revenu_disponible', 2017)
        """
    if condition is None:
        condition = True
    variable = simulation.tax_benefit_system.get_variable(variable_name)
    population = simulation.get_variable_population(variable_name)
    value = (np.random.rand(population.count) * max_value * condition).astype(variable.dtype)
    simulation.set_input(variable_name, period, value)
