import numpy as np
from numpy.testing import assert_array_equal

from .test_entities import TEST_CASE, new_simulation

def test_ind_sub_pop():
    simulation = new_simulation(TEST_CASE)
    age = np.asarray([40, 37, 7, 19, 54, 16])
    subpop = simulation.persons.get_subpopulation(age >= 18)


    assert_array_equal(subpop.ids, ['ind0', 'ind1', 'ind3', 'ind4'])
    assert_array_equal(subpop.has_role(simulation.household.entity.PARENT), [True, True, False, True])


def test_household_sub_pop():
    test_case = {
        'persons': {'ind0': {}, 'ind1': {}, 'ind2': {}, 'ind3': {}, 'ind4': {}, 'ind5': {}, 'ind6': {}},
        'households': {
            'h1': {'children': ['ind2', 'ind3'], 'parents': ['ind0', 'ind1']},
            'h3': {'parents': ['ind6']},
            'h2': {'children': ['ind5'], 'parents': ['ind4']},
            },
        }

    period = '2019-01'
    simulation = new_simulation(test_case)
    simulation.set_input('age', period, np.asarray([40, 37, 7, 19, 54, 16, 30]))

    condition = simulation.household.nb_persons() > 1
    households = simulation.household.get_subpopulation(condition)

    age = households.members('age', period)
    assert_array_equal(age, [40, 37, 7, 19, 54, 16])

    assert_array_equal(households.members_entity_id, [0, 0, 0, 0, 1, 1])
    assert_array_equal(households.members_role, simulation.household.members_role[:-1])
    assert_array_equal(households.members_position, simulation.household.members_position[:-1])

    assert_array_equal(households.sum(age), [40 + 37 + 19 + 7, 54 + 16])
    assert_array_equal(households.any(age > 50), [False, True])
