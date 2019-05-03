import numpy as np

from openfisca_core.populations import SubPopulation, GroupSubPopulation

from .test_entities import TEST_CASE, new_simulation

def test_ind_sub_pop():
    simulation = new_simulation(TEST_CASE)
    age = np.asarray([40, 37, 7, 19, 54, 16])
    subpop = SubPopulation(simulation.persons, age >= 18)


    assert (subpop.ids == ['ind0', 'ind1', 'ind3', 'ind4']).all()
    assert (subpop.has_role(simulation.household.entity.PARENT) == [True, True, False, True]).all()


def test_household_sub_pop():
    test_case = {
        'persons': {'ind0': {}, 'ind1': {}, 'ind2': {}, 'ind3': {}, 'ind4': {}, 'ind5': {}, 'ind6': {}},
        'households': {
            'h1': {'children': ['ind2', 'ind3'], 'parents': ['ind0', 'ind1']},
            'h2': {'children': ['ind5'], 'parents': ['ind4']},
            'h3': {'parents': ['ind6']}
            },
        }

    period = '2019-01'
    simulation = new_simulation(test_case)
    simulation.set_input('age', period, np.asarray([40, 37, 7, 19, 54, 16, 30]))

    condition = simulation.household.nb_persons() > 1
    households = GroupSubPopulation(simulation.household, condition)

    age = households.members('age', period)
    assert (age == [40, 37, 7, 19, 54, 16]).all()

    assert (households.members_entity_id == simulation.household.members_entity_id[:-1]).all()
    assert (households.members_role == simulation.household.members_role[:-1]).all()
    assert (households.members_position == simulation.household.members_position[:-1]).all()

    assert (households.sum(age) == [40 + 37 + 19 + 7, 54 + 16]).all()
    assert (households.any(age > 50) == [False, True]).all()

