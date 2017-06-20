# -*- coding: utf-8 -*-

from copy import deepcopy

from openfisca_core.tools import assert_near
from openfisca_core.simulations import Simulation
from openfisca_country_template.entities import Household
from test_countries import tax_benefit_system

TEST_CASE = {
    'persons': [{'id': 'ind0'}, {'id': 'ind1'}, {'id': 'ind2'}, {'id': 'ind3'}, {'id': 'ind4'}, {'id': 'ind5'}],
    'households': [
        {'children': ['ind2', 'ind3'], 'parents': ['ind0', 'ind1']},
        {'children': ['ind5'], 'parents': ['ind4']}
        ],
    }

TEST_CASE_AGES = deepcopy(TEST_CASE)
AGES = [40, 37, 7, 9, 54, 20]
for (individu, age) in zip(TEST_CASE_AGES['persons'], AGES):
        individu['age'] = age

FIRST_PARENT = Household.FIRST_PARENT
SECOND_PARENT = Household.SECOND_PARENT
PARENT = Household.PARENT
CHILD = Household.CHILD

YEAR = 2016
MONTH = "2016-01"


def new_simulation(test_case, period = MONTH):
    return tax_benefit_system.new_scenario().init_from_test_case(
        period = period,
        test_case = test_case
        ).new_simulation()


def test_role_index_and_positions():
    simulation = new_simulation(TEST_CASE)
    assert_near(simulation.household.members_entity_id, [0, 0, 0, 0, 1, 1])
    assert((simulation.household.members_role == [FIRST_PARENT, SECOND_PARENT, CHILD, CHILD, FIRST_PARENT, CHILD]).all())
    assert_near(simulation.household.members_legacy_role, [0, 1, 2, 3, 0, 2])
    assert_near(simulation.household.members_position, [0, 1, 2, 3, 0, 1])
    assert(simulation.person.ids == ["ind0", "ind1", "ind2", "ind3", "ind4", "ind5"])
    assert(simulation.household.ids == [0, 1])


def test_entity_structure_with_constructor():
    simulation_json = {
        "persons": {
            "bill": {},
            "bob": {},
            "claudia": {},
            "janet": {},
            "tom": {},
            },
        "households": {
            "first_household": {
                "parents": ['bill', 'bob'],
                "children": ['janet', 'tom']
                },
            "second_household": {
                "parents": ["claudia"]
                }
            }
        }

    simulation = Simulation(tax_benefit_system = tax_benefit_system, simulation_json = simulation_json)
    household = simulation.household

    assert_near(household.members_entity_id, [0, 0, 1, 0, 0])
    assert((household.members_role == [FIRST_PARENT, SECOND_PARENT, FIRST_PARENT, CHILD, CHILD]).all())
    assert_near(household.members_legacy_role, [0, 1, 0, 2, 3])
    assert_near(household.members_position, [0, 1, 0, 2, 3])


def test_entity_variables_with_constructor():
    simulation_json = {
        "persons": {
            "bill": {},
            "bob": {},
            "claudia": {},
            "janet": {},
            "tom": {},
            },
        "households": {
            "first_household": {
                "parents": ['bill', 'bob'],
                "children": ['janet', 'tom'],
                "rent": {"2017-06": 800}
                },
            "second_household": {
                "parents": ["claudia"],
                "rent": {"2017-06": 600}
                }
            }
        }

    simulation = Simulation(tax_benefit_system = tax_benefit_system, simulation_json = simulation_json)
    household = simulation.household
    assert_near(household('rent', "2017-06"), [800, 600])


def test_person_variable_with_constructor():
    simulation_json = {
        "persons": {
            "bill": {
                "salary": {
                    "2017-11": 1500,
                    "2017-12": 2000
                    }
                },
            "bob": {
                "salary": {}
                },
            "claudia": {
                "salary": {
                    "2017-11": 3000,
                    "2017-12": 4000
                    }
                },
            "janet": {},
            "tom": {},
            },
        "households": {
            "first_household": {
                "parents": ['bill', 'bob'],
                "children": ['janet', 'tom'],
                },
            "second_household": {
                "parents": ["claudia"],
                }
            }
        }
    simulation = Simulation(tax_benefit_system = tax_benefit_system, simulation_json = simulation_json)
    person = simulation.person
    assert_near(person('salary', "2017-11"), [1500, 0, 3000, 0, 0])
    assert_near(person('salary', "2017-12"), [2000, 0, 4000, 0, 0])


def test_set_input():
    simulation_json = {
        "persons": {
            "bill": {
                "salary": {
                    "2017": 24000,
                    "2017-11": 2000,
                    "2017-12": 2000

                    }
                },
            "bob": {
                "salary": {
                    "2017": 30000,
                    "2017-11": 0,
                    "2017-12": 0
                    }
                },
            "claudia": {
                "salary": {
                    "2017": 24000,
                    "2017-11": 4000,
                    "2017-12": 4000,
                    }
                },
            "janet": {},
            "tom": {},
            },
        "households": {
            "first_household": {
                "parents": ['bill', 'bob'],
                "children": ['janet', 'tom'],
                },
            "second_household": {
                "parents": ["claudia"],
                }
            }
        }

    simulation = Simulation(tax_benefit_system = tax_benefit_system, simulation_json = simulation_json)
    person = simulation.person
    assert_near(person('salary', "2017-12"), [2000, 0, 4000, 0, 0])
    assert_near(person('salary', "2017-10"), [2000, 3000, 1600, 0, 0])


def test_has_role():
    simulation = new_simulation(TEST_CASE)
    individu = simulation.persons
    assert_near(individu.has_role(CHILD), [False, False, True, True, False, True])


def test_has_role_with_subrole():
    simulation = new_simulation(TEST_CASE)
    individu = simulation.persons
    assert_near(individu.has_role(PARENT), [True, True, False, False, True, False])
    assert_near(individu.has_role(FIRST_PARENT), [True, False, False, False, True, False])
    assert_near(individu.has_role(SECOND_PARENT), [False, True, False, False, False, False])


def test_project():
    test_case = deepcopy(TEST_CASE)
    test_case['households'][0]['housing_tax'] = 20000

    simulation = new_simulation(test_case, YEAR)
    household = simulation.household

    housing_tax = household('housing_tax', YEAR)
    projected_housing_tax = household.project(housing_tax)

    assert_near(projected_housing_tax, [20000, 20000, 20000, 20000, 0, 0])

    housing_tax_projected_on_parents = household.project(housing_tax, role = PARENT)
    assert_near(housing_tax_projected_on_parents, [20000, 20000, 0, 0, 0, 0])


def test_implicit_projection():
    test_case = deepcopy(TEST_CASE)
    test_case['households'][0]['housing_tax'] = 20000

    simulation = new_simulation(test_case, YEAR)
    individu = simulation.person
    housing_tax = individu.household('housing_tax', YEAR)

    assert_near(housing_tax, [20000, 20000, 20000, 20000, 0, 0])


def test_project_on_first_person():
    test_case = deepcopy(TEST_CASE)
    test_case['households'][0]['housing_tax'] = 20000
    test_case['households'][1]['housing_tax'] = 5000

    simulation = new_simulation(test_case, YEAR)
    household = simulation.household

    housing_tax = household('housing_tax', YEAR)
    projected_housing_tax = household.project_on_first_person(housing_tax)

    assert_near(projected_housing_tax, [20000, 0, 0, 0, 5000, 0])


def test_share_between_members():
    test_case = deepcopy(TEST_CASE)
    test_case['households'][0]['housing_tax'] = 20000
    test_case['households'][1]['housing_tax'] = 5000

    simulation = new_simulation(test_case, YEAR)
    household = simulation.household

    housing_tax = household('housing_tax', YEAR)

    housing_tax_shared = household.share_between_members(housing_tax, role = PARENT)

    assert_near(housing_tax_shared, [10000, 10000, 0, 0, 5000, 0])


def test_sum():
    test_case = deepcopy(TEST_CASE)
    test_case['persons'][0]['salary'] = 1000
    test_case['persons'][1]['salary'] = 1500
    test_case['persons'][4]['salary'] = 3000
    test_case['persons'][5]['salary'] = 500

    simulation = new_simulation(test_case, MONTH)
    household = simulation.household

    salary = household.members('salary', "2016-01")
    total_salary_by_household = household.sum(salary)

    assert_near(total_salary_by_household, [2500, 3500])

    total_salary_parents_by_household = household.sum(salary, role = PARENT)

    assert_near(total_salary_parents_by_household, [2500, 3000])


def test_any():
    test_case = deepcopy(TEST_CASE_AGES)
    simulation = new_simulation(test_case)
    household = simulation.household

    age = household.members('age', period = MONTH)
    condition_age = (age <= 18)
    has_household_member_with_age_inf_18 = household.any(condition_age)
    assert_near(has_household_member_with_age_inf_18, [True, False])

    condition_age_2 = (age > 18)
    has_household_CHILD_with_age_sup_18 = household.any(condition_age_2, role = CHILD)
    assert_near(has_household_CHILD_with_age_sup_18, [False, True])


def test_all():
    test_case = deepcopy(TEST_CASE_AGES)
    simulation = new_simulation(test_case)
    household = simulation.household

    age = household.members('age', period = MONTH)

    condition_age = (age >= 18)
    all_persons_age_sup_18 = household.all(condition_age)
    assert_near(all_persons_age_sup_18, [False, True])

    all_parents_age_sup_18 = household.all(condition_age, role = PARENT)
    assert_near(all_parents_age_sup_18, [True, True])


def test_max():
    test_case = deepcopy(TEST_CASE_AGES)
    simulation = new_simulation(test_case)
    household = simulation.household

    age = household.members('age', period = MONTH)

    age_max = household.max(age)
    assert_near(age_max, [40, 54])

    age_max_child = household.max(age, role = CHILD)
    assert_near(age_max_child, [9, 20])


def test_min():
    test_case = deepcopy(TEST_CASE_AGES)
    simulation = new_simulation(test_case)
    household = simulation.household

    age = household.members('age', period = MONTH)

    age_min = household.min(age)
    assert_near(age_min, [7, 20])

    age_min_parents = household.min(age, role = PARENT)
    assert_near(age_min_parents, [37, 54])


def test_partner():
    test_case = deepcopy(TEST_CASE)
    test_case['persons'][0]['salary'] = 1000
    test_case['persons'][1]['salary'] = 1500
    test_case['persons'][4]['salary'] = 3000
    test_case['persons'][5]['salary'] = 500

    simulation = new_simulation(test_case)
    persons = simulation.persons

    salary = persons('salary', period = MONTH)

    salary_second_parent = persons.value_from_partner(salary, persons.household, PARENT)

    assert_near(salary_second_parent, [1500, 1000, 0, 0, 0, 0])


def test_value_from_first_person():
    test_case = deepcopy(TEST_CASE)
    test_case['persons'][0]['salary'] = 1000
    test_case['persons'][1]['salary'] = 1500
    test_case['persons'][4]['salary'] = 3000
    test_case['persons'][5]['salary'] = 500

    simulation = new_simulation(test_case)
    household = simulation.household

    salaries = household.members('salary', period = MONTH)
    salary_first_person = household.value_from_first_person(salaries)

    assert_near(salary_first_person, [1000, 3000])


def test_sum_following_bug_ipp_1():
    test_case = {
        'persons': [{'id': 'ind0'}, {'id': 'ind1'}, {'id': 'ind2'}, {'id': 'ind3'}],
        'households': [
            {'parents': ['ind0']},
            {'parents': ['ind1'], 'children': ['ind2', 'ind3']}
            ],
        }
    test_case['persons'][0]['salary'] = 2000
    test_case['persons'][1]['salary'] = 2000
    test_case['persons'][2]['salary'] = 1000
    test_case['persons'][3]['salary'] = 1000

    simulation = new_simulation(test_case)
    household = simulation.household

    eligible_i = household.members('salary', period = MONTH) < 1500
    nb_eligibles_by_household = household.sum(eligible_i, role = CHILD)

    assert_near(nb_eligibles_by_household, [0, 2])


def test_sum_following_bug_ipp_2():
    test_case = {
        'persons': [{'id': 'ind0'}, {'id': 'ind1'}, {'id': 'ind2'}, {'id': 'ind3'}],
        'households': [
            {'parents': ['ind1'], 'children': ['ind2', 'ind3']},
            {'parents': ['ind0']}
            ],
        }
    test_case['persons'][0]['salary'] = 2000
    test_case['persons'][1]['salary'] = 2000
    test_case['persons'][2]['salary'] = 1000
    test_case['persons'][3]['salary'] = 1000

    simulation = new_simulation(test_case)
    household = simulation.household

    eligible_i = household.members('salary', period = MONTH) < 1500
    nb_eligibles_by_household = household.sum(eligible_i, role = CHILD)

    assert_near(nb_eligibles_by_household, [2, 0])
