"""Tests for the condition parameter on GroupPopulation aggregation methods.

Verifies that sum, any, all, min, max, nb_persons accept a `condition`
keyword argument and produce correct results when combined with `role`.
"""

from copy import deepcopy

import pytest

from openfisca_core import tools
from openfisca_core.simulations import SimulationBuilder

# -- Fixtures ---------------------------------------------------------------

TEST_CASE = {
    "persons": {"ind0": {}, "ind1": {}, "ind2": {}, "ind3": {}, "ind4": {}, "ind5": {}},
    "households": {
        "h1": {"children": ["ind2", "ind3"], "adults": ["ind0", "ind1"]},
        "h2": {"children": ["ind5"], "adults": ["ind4"]},
    },
}

TEST_CASE_AGES = deepcopy(TEST_CASE)
AGES = [40, 37, 7, 9, 54, 20]
for _ind, _age in zip(TEST_CASE_AGES["persons"].values(), AGES):
    _ind["age"] = _age

MONTH = "2016-01"
YEAR = 2016


@pytest.fixture
def sim(tax_benefit_system):
    test_case = deepcopy(TEST_CASE_AGES)
    test_case["persons"]["ind0"]["salary"] = 1000
    test_case["persons"]["ind1"]["salary"] = 1500
    test_case["persons"]["ind2"]["salary"] = 200
    test_case["persons"]["ind3"]["salary"] = 300
    test_case["persons"]["ind4"]["salary"] = 3000
    test_case["persons"]["ind5"]["salary"] = 500
    sb = SimulationBuilder()
    sb.set_default_period(MONTH)
    return sb.build_from_entities(tax_benefit_system, test_case)


# -- Tests -------------------------------------------------------------------


class TestSumWithCondition:
    def test_sum_condition_only(self, sim):
        household = sim.household
        salary = household.members("salary", MONTH)
        age = household.members("age", MONTH)
        is_adult = age >= 18

        result = household.sum(salary, condition=is_adult)
        # h1: ind0(1000, 40) + ind1(1500, 37) = 2500 (children excluded: ind2 age 7, ind3 age 9)
        # h2: ind4(3000, 54) + ind5(500, 20) = 3500 (both adults)
        tools.assert_near(result, [2500, 3500])

    def test_sum_role_and_condition(self, sim):
        from openfisca_country_template import entities

        CHILD = entities.Household.CHILD

        household = sim.household
        salary = household.members("salary", MONTH)
        age = household.members("age", MONTH)
        is_older_than_8 = age > 8

        result = household.sum(salary, role=CHILD, condition=is_older_than_8)
        # h1 children: ind2(200, age 7 → excluded), ind3(300, age 9 → included) = 300
        # h2 children: ind5(500, age 20 → included) = 500
        tools.assert_near(result, [300, 500])


class TestAnyWithCondition:
    def test_any_condition_only(self, sim):
        household = sim.household
        salary = household.members("salary", MONTH)
        age = household.members("age", MONTH)
        is_child = age < 18

        # Any child with salary > 250?
        result = household.any(salary > 250, condition=is_child)
        # h1: ind2(200 → no), ind3(300 → yes) → True
        # h2: ind5(500 → yes, but age 20 → not a child) → False
        tools.assert_near(result, [True, False])


class TestAllWithCondition:
    def test_all_condition_only(self, sim):
        household = sim.household
        salary = household.members("salary", MONTH)
        age = household.members("age", MONTH)
        is_adult = age >= 18

        # All adults have salary >= 1000?
        result = household.all(salary >= 1000, condition=is_adult)
        # h1: ind0(1000 → yes), ind1(1500 → yes) → True
        # h2: ind4(3000 → yes), ind5(500 → no) → False
        tools.assert_near(result, [True, False])


class TestMinMaxWithCondition:
    def test_min_condition_only(self, sim):
        household = sim.household
        salary = household.members("salary", MONTH)
        age = household.members("age", MONTH)
        is_adult = age >= 18

        result = household.min(salary, condition=is_adult)
        # h1: min(1000, 1500) = 1000
        # h2: min(3000, 500) = 500
        tools.assert_near(result, [1000, 500])

    def test_max_condition_only(self, sim):
        household = sim.household
        salary = household.members("salary", MONTH)
        age = household.members("age", MONTH)
        is_adult = age >= 18

        result = household.max(salary, condition=is_adult)
        # h1: max(1000, 1500) = 1500
        # h2: max(3000, 500) = 3000
        tools.assert_near(result, [1500, 3000])


class TestNbPersonsWithCondition:
    def test_nb_persons_condition_only(self, sim):
        household = sim.household
        age = household.members("age", MONTH)
        is_adult = age >= 18

        result = household.nb_persons(condition=is_adult)
        # h1: ind0(40), ind1(37) → 2 adults
        # h2: ind4(54), ind5(20) → 2 adults
        tools.assert_near(result, [2, 2])

    def test_nb_persons_role_and_condition(self, sim):
        from openfisca_country_template import entities

        CHILD = entities.Household.CHILD

        household = sim.household
        salary = household.members("salary", MONTH)
        has_income = salary > 0

        result = household.nb_persons(role=CHILD, condition=has_income)
        # h1 children: ind2(200 → yes), ind3(300 → yes) → 2
        # h2 children: ind5(500 → yes) → 1
        tools.assert_near(result, [2, 1])


class TestBackwardCompatibility:
    """Every existing call without condition should still work identically."""

    def test_sum_without_condition(self, sim):
        household = sim.household
        salary = household.members("salary", MONTH)
        result = household.sum(salary)
        tools.assert_near(result, [3000, 3500])

    def test_min_without_condition(self, sim):
        household = sim.household
        age = household.members("age", MONTH)
        result = household.min(age)
        tools.assert_near(result, [7, 20])

    def test_max_without_condition(self, sim):
        household = sim.household
        age = household.members("age", MONTH)
        result = household.max(age)
        tools.assert_near(result, [40, 54])

    def test_nb_persons_without_condition(self, sim):
        household = sim.household
        tools.assert_near(household.nb_persons(), [4, 2])
