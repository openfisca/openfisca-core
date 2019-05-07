import numpy as np
from numpy.testing import assert_array_equal
from pytest import fixture

from openfisca_core.periods import period as make_period

from .test_entities import new_simulation, FIRST_PARENT, SECOND_PARENT, PARENT, CHILD

period = make_period('2019-01')


@fixture
def simulation():
    return new_simulation({
        'persons': {'ind0': {}, 'ind1': {}, 'ind2': {}, 'ind3': {}, 'ind4': {}, 'ind5': {}},
        'households': {
            'h1': {'children': ['ind2', 'ind3'], 'parents': ['ind0', 'ind1']},
            'h2': {'children': ['ind5'], 'parents': ['ind4']},
            },
        })


@fixture
def p_subpop(simulation):
    condition = np.asarray([True, True, False, True, True, False])
    return simulation.persons.get_subpopulation(condition)


@fixture
def p_subpop_2(simulation):
    condition_2 = np.asarray([True, True, True, False, False, False])
    return simulation.persons.get_subpopulation(condition_2)


def test_ids(p_subpop):
    assert_array_equal(p_subpop.ids, ['ind0', 'ind1', 'ind3', 'ind4'])


def test_has_role(p_subpop):
    assert_array_equal(p_subpop.has_role(PARENT), [True, True, False, True])


def test_default_array(p_subpop):
    assert_array_equal(p_subpop.default_array('salary'), [0, 0, 0, 0])


def test_cache_global_write_subpop_read(simulation, p_subpop):
    simulation.set_input('salary', period, [1000, 2000, 0, 1200, 2400, 800])

    cached_array_subpop = p_subpop.get_cached_array('salary', period)
    assert_array_equal(cached_array_subpop.value, [1000, 2000, 1200, 2400])
    assert cached_array_subpop.mask is None


def test_cache_subpop_write_global_read(simulation, p_subpop):
    p_subpop.put_in_cache('salary', period, [1000, 2000, 1200, 2400])
    cached_array = simulation.persons.get_cached_array('salary', period)

    assert_array_equal(cached_array.value, [1000, 2000, 1200, 2400])
    assert_array_equal(cached_array.mask, p_subpop.condition)


def test_cache_subpop_write_subpop_read(p_subpop, p_subpop_2):
    p_subpop.put_in_cache('salary', period, [1000, 2000, 1200, 2400])

    cached_array = p_subpop_2.get_cached_array('salary', period)
    assert_array_equal(cached_array.value, [1000, 2000])
    assert_array_equal(cached_array.mask, [True, True, False])


def test_cache_2_subpop_write_global_read(simulation, p_subpop, p_subpop_2):
    p_subpop.put_in_cache('salary', period, np.asarray([1000, 2000, 1200, 2400]))
    p_subpop_2.put_in_cache('salary', period, np.asarray([1000, 2000, 0]))

    cached_array = simulation.persons.get_cached_array('salary', period)

    assert_array_equal(cached_array.value, [1000, 2000, 0, 1200, 2400])
    assert_array_equal(cached_array.mask, [True, True, True, True, True, False])


def test_cache_disjunct_pop(simulation, p_subpop):
    p_subpop.put_in_cache('salary', period, [1000, 2000, 1200, 2400])
    p_subpop_2 = simulation.persons.get_subpopulation(np.asarray([False, False, True, False, False, False]))

    assert p_subpop_2.get_cached_array('salary', period) is None


def test_sub_subpopulation(p_subpop):
    p_subpop_3 = p_subpop.get_subpopulation([True, False, True, False])
    assert_array_equal(
        p_subpop_3.condition,
        [True, False, False, True, False, False]
        )


def test_global_calculation(simulation, p_subpop):
    p_subpop.put_in_cache('salary', period, [1000, 2000, 1200, 2400])

    assert_array_equal(
        simulation.calculate('salary', period),
        [1000, 2000, 0, 1200, 2400, 0]
        )


def test_subpop_calculation(simulation, p_subpop):
    simulation.set_input('salary', period, [1000, 2000, 0, 1200, 2400, 800])
    assert_array_equal(
        p_subpop('salary', period),
        [1000, 2000, 1200, 2400]
        )


def test_subpop_calculation_subpop_init(p_subpop, p_subpop_2):
    p_subpop.put_in_cache('salary', period, np.asarray([1000, 2000, 1200, 2400]))
    assert_array_equal(
        p_subpop_2('salary', period),
        [1000, 2000, 0]
        )


@fixture
def simulation_h():
    test_case = {
        'persons': {'ind0': {}, 'ind1': {}, 'ind2': {}, 'ind3': {}, 'ind4': {}, 'ind5': {}, 'ind6': {}},
        'households': {
            'h1': {'children': ['ind2', 'ind3'], 'parents': ['ind0', 'ind1']},
            'h3': {'parents': ['ind4']},
            'h2': {'children': ['ind6'], 'parents': ['ind5']},
            },
        }
    return new_simulation(test_case)


@fixture
def h_subpop(simulation_h):
    return simulation_h.household.get_subpopulation(np.asarray([True, False, True]))


def test_household_sub_pop(h_subpop):
    assert_array_equal(h_subpop.members_entity_id, [0, 0, 0, 0, 1, 1])
    assert_array_equal(h_subpop.members_role, [FIRST_PARENT, SECOND_PARENT, CHILD, CHILD, FIRST_PARENT, CHILD])
    assert_array_equal(h_subpop.members_position, [0, 1, 2, 3, 0, 1])


def test_household_sub_pop_members(h_subpop):
    assert_array_equal(
        h_subpop.members.condition,
        [True, True, True, True, False, True, True]
        )


def test_aggregation(simulation_h, h_subpop):
    simulation_h.set_input('age', period, np.asarray([40, 37, 7, 19, 30, 54, 16]))
    age = h_subpop.members('age', period)

    assert_array_equal(h_subpop.sum(age), [40 + 37 + 19 + 7, 54 + 16])
    assert_array_equal(h_subpop.any(age > 50), [False, True])
    assert_array_equal(h_subpop.max(age), [40, 54])


def test_projection_p_to_h(simulation_h, h_subpop):
    simulation_h.set_input('age', period, np.asarray([40, 37, 7, 19, 30, 54, 16]))

    assert_array_equal(
        h_subpop.first_parent('age', period),
        [40, 54]
        )


def test_projection_h_to_p(simulation_h, h_subpop):
    simulation_h.set_input('housing_tax', 2019, np.asarray([500, 400, 600]))
    p_subpop = simulation_h.persons.get_subpopulation(np.asarray([True, True, True, False, True, True, True]))

    assert_array_equal(
        p_subpop.household.ids,
        ['h1', 'h1', 'h1', 'h3', 'h2', 'h2']
        )
    assert_array_equal(
        p_subpop.household('housing_tax', 2019),
        [500, 500, 500, 400, 600, 600]
        )


def test_projection_h_to_p_2(simulation_h, h_subpop):
    simulation_h.set_input('housing_tax', 2019, np.asarray([500, 400, 600]))
    p_subpop = simulation_h.persons.get_subpopulation(np.asarray([True, True, True, True, False, True, True]))

    assert_array_equal(
        p_subpop.household.ids,
        ['h1', 'h1', 'h1', 'h1', 'h2', 'h2']
        )
    assert_array_equal(
        p_subpop.household('housing_tax', 2019),
        [500, 500, 500, 500, 600, 600]
        )


def test_trace(simulation, p_subpop):
    simulation.trace = True
    simulation.set_input('salary', period, [1000, 2000, 0, 1200, 2400, 800])
    p_subpop('income_tax', period)
    traced_value = list(simulation.tracer.trace.values())[0]['value']
    assert traced_value.size == simulation.persons.count


def test_trace_2(simulation, p_subpop):
    simulation.trace = True
    p_subpop('disposable_income', period)
    traced_value = list(simulation.tracer.trace.values())[0]['value']
    assert traced_value.size == simulation.persons.count
