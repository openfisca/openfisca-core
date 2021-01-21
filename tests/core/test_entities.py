# -*- coding: utf-8 -*-

from pytest import fixture

from openfisca_core.tools import assert_near
from openfisca_core.tools.test_runner import yaml
from openfisca_country_template.entities import Household


@fixture
def case():
    return {
        'persons': {'ind0': {}, 'ind1': {}, 'ind2': {}, 'ind3': {}, 'ind4': {}, 'ind5': {}},
        'households': {
            'h1': {'children': ['ind2', 'ind3'], 'parents': ['ind0', 'ind1']},
            'h2': {'children': ['ind5'], 'parents': ['ind4']}
            },
        }


@fixture
def ages_case(case):
    AGES = [40, 37, 7, 9, 54, 20]
    for (individu, age) in zip(case['persons'].values(), AGES):
        individu['age'] = age
    return case


FIRST_PARENT = Household.FIRST_PARENT
SECOND_PARENT = Household.SECOND_PARENT
PARENT = Household.PARENT
CHILD = Household.CHILD


@fixture 
def make_simulation_from_yaml(tax_benefit_system, simulation_builder):
    def _make_simulation_from_yaml(simulation_yaml):
        return simulation_builder.build_from_dict(tax_benefit_system, yaml.safe_load(simulation_yaml))
    return _make_simulation_from_yaml


@fixture 
def make_simulation_from_entities(tax_benefit_system, simulation_builder, period):
    def _make_simulation_from_enties(entities, period=period):
        simulation_builder.set_default_period(period)
        return simulation_builder.build_from_entities(tax_benefit_system, entities)
    return _make_simulation_from_enties

@fixture
def simulation_case(make_simulation_from_entities, case):
    return make_simulation_from_entities(case)


def test_role_index_and_positions(simulation_case):
    assert_near(simulation_case.household.members_entity_id, [0, 0, 0, 0, 1, 1])
    assert((simulation_case.household.members_role == [FIRST_PARENT, SECOND_PARENT, CHILD, CHILD, FIRST_PARENT, CHILD]).all())
    assert_near(simulation_case.household.members_position, [0, 1, 2, 3, 0, 1])
    assert(simulation_case.person.ids == ["ind0", "ind1", "ind2", "ind3", "ind4", "ind5"])
    assert(simulation_case.household.ids == ['h1', 'h2'])


def test_entity_structure_with_constructor(make_simulation_from_yaml):
    simulation  = make_simulation_from_yaml("""
        persons:
          bill: {}
          bob: {}
          claudia: {}
          janet: {}
          tom: {}
        households:
          first_household:
            parents:
            - bill
            - bob
            children:
            - janet
            - tom
          second_household:
            parents:
            - claudia
    """)

    household = simulation.household

    assert_near(household.members_entity_id, [0, 0, 1, 0, 0])
    assert((household.members_role == [FIRST_PARENT, SECOND_PARENT, FIRST_PARENT, CHILD, CHILD]).all())
    assert_near(household.members_position, [0, 1, 0, 2, 3])


def test_entity_variables_with_constructor(make_simulation_from_yaml):
    simulation = make_simulation_from_yaml("""
        persons:
          bill: {}
          bob: {}
          claudia: {}
          janet: {}
          tom: {}
        households:
          first_household:
            parents:
            - bill
            - bob
            children:
            - janet
            - tom
            rent:
              2017-06: 800
          second_household:
            parents:
            - claudia
            rent:
              2017-06: 600
    """)

    household = simulation.household
    assert_near(household('rent', "2017-06"), [800, 600])


def test_person_variable_with_constructor(make_simulation_from_yaml):
    simulation = make_simulation_from_yaml("""
        persons:
          bill:
            salary:
              2017-11: 1500
              2017-12: 2000
          bob:
            salary: {}
          claudia:
            salary:
              2017-11: 3000
              2017-12: 4000
          janet: {}
          tom: {}
        households:
          first_household:
            parents:
            - bill
            - bob
            children:
            - janet
            - tom
          second_household:
            parents:
            - claudia
    """)

    person = simulation.person
    assert_near(person('salary', "2017-11"), [1500, 0, 3000, 0, 0])
    assert_near(person('salary', "2017-12"), [2000, 0, 4000, 0, 0])


def test_set_input_with_constructor(make_simulation_from_yaml):
    simulation = make_simulation_from_yaml("""
        persons:
          bill:
            salary:
              '2017': 24000
              2017-11: 2000
              2017-12: 2000
          bob:
            salary:
              '2017': 30000
              2017-11: 0
              2017-12: 0
          claudia:
            salary:
              '2017': 24000
              2017-11: 4000
              2017-12: 4000
          janet: {}
          tom: {}
        households:
          first_household:
            parents:
            - bill
            - bob
            children:
            - janet
            - tom
          second_household:
            parents:
            - claudia
    """)

    person = simulation.person
    assert_near(person('salary', "2017-12"), [2000, 0, 4000, 0, 0])
    assert_near(person('salary', "2017-10"), [2000, 3000, 1600, 0, 0])


def test_has_role(simulation_case):
    individu = simulation_case.persons
    assert_near(individu.has_role(CHILD), [False, False, True, True, False, True])


def test_has_role_with_subrole(simulation_case):
    individu = simulation_case.persons
    assert_near(individu.has_role(PARENT), [True, True, False, False, True, False])
    assert_near(individu.has_role(FIRST_PARENT), [True, False, False, False, True, False])
    assert_near(individu.has_role(SECOND_PARENT), [False, True, False, False, False, False])


def test_project(make_simulation_from_entities, case, year_period):
    case['households']['h1']['housing_tax'] = 20000

    simulation = make_simulation_from_entities(case, year_period)
    household = simulation.household

    housing_tax = household('housing_tax', year_period)
    projected_housing_tax = household.project(housing_tax)

    assert_near(projected_housing_tax, [20000, 20000, 20000, 20000, 0, 0])

    housing_tax_projected_on_parents = household.project(housing_tax, role = PARENT)
    assert_near(housing_tax_projected_on_parents, [20000, 20000, 0, 0, 0, 0])


def test_implicit_projection(make_simulation_from_entities, case, year_period):
    case['households']['h1']['housing_tax'] = 20000

    simulation = make_simulation_from_entities(case, year_period)
    individu = simulation.person
    housing_tax = individu.household('housing_tax', year_period)

    assert_near(housing_tax, [20000, 20000, 20000, 20000, 0, 0])


def test_sum(make_simulation_from_entities, case, period):
    case['persons']['ind0']['salary'] = 1000
    case['persons']['ind1']['salary'] = 1500
    case['persons']['ind4']['salary'] = 3000
    case['persons']['ind5']['salary'] = 500

    simulation = make_simulation_from_entities(case, period)
    household = simulation.household

    salary = household.members('salary', "2016-01")
    total_salary_by_household = household.sum(salary)

    assert_near(total_salary_by_household, [2500, 3500])

    total_salary_parents_by_household = household.sum(salary, role = PARENT)

    assert_near(total_salary_parents_by_household, [2500, 3000])


def test_any(make_simulation_from_entities, ages_case, period):
    simulation = make_simulation_from_entities(ages_case)
    household = simulation.household

    age = household.members('age', period = period)
    condition_age = (age <= 18)
    has_household_member_with_age_inf_18 = household.any(condition_age)
    assert_near(has_household_member_with_age_inf_18, [True, False])

    condition_age_2 = (age > 18)
    has_household_CHILD_with_age_sup_18 = household.any(condition_age_2, role = CHILD)
    assert_near(has_household_CHILD_with_age_sup_18, [False, True])


def test_all(make_simulation_from_entities, ages_case, period):
    simulation = make_simulation_from_entities(ages_case)
    household = simulation.household

    age = household.members('age', period = period)

    condition_age = (age >= 18)
    all_persons_age_sup_18 = household.all(condition_age)
    assert_near(all_persons_age_sup_18, [False, True])

    all_parents_age_sup_18 = household.all(condition_age, role = PARENT)
    assert_near(all_parents_age_sup_18, [True, True])


def test_max(make_simulation_from_entities, ages_case, period):
    simulation = make_simulation_from_entities(ages_case)
    household = simulation.household

    age = household.members('age', period = period)

    age_max = household.max(age)
    assert_near(age_max, [40, 54])

    age_max_child = household.max(age, role = CHILD)
    assert_near(age_max_child, [9, 20])


def test_min(make_simulation_from_entities, ages_case, period):
    simulation = make_simulation_from_entities(ages_case)
    household = simulation.household

    age = household.members('age', period = period)

    age_min = household.min(age)
    assert_near(age_min, [7, 20])

    age_min_parents = household.min(age, role = PARENT)
    assert_near(age_min_parents, [37, 54])


def test_value_nth_person(make_simulation_from_entities, ages_case, period):
    simulation = make_simulation_from_entities(test_case, ages_case)
    household = simulation.household
    array = household.members('age', period)

    result0 = household.value_nth_person(0, array, default=-1)
    assert_near(result0, [40, 54])

    result1 = household.value_nth_person(1, array, default=-1)
    assert_near(result1, [37, 20])

    result2 = household.value_nth_person(2, array, default=-1)
    assert_near(result2, [7, -1])

    result3 = household.value_nth_person(3, array, default=-1)
    assert_near(result3, [9, -1])


def test_rank(make_simulation_from_entities, ages_case, period):
    simulation = make_simulation_from_entities(ages_case)
    person = simulation.person

    age = person('age', period)  # [40, 37, 7, 9, 54, 20]
    rank = person.get_rank(person.household, age)
    assert_near(rank, [3, 2, 0, 1, 1, 0])

    rank_in_siblings = person.get_rank(person.household, - age, condition = person.has_role(Household.CHILD))
    assert_near(rank_in_siblings, [-1, -1, 1, 0, -1, 0])


def test_partner(make_simulation_from_entities, case, period):
    case['persons']['ind0']['salary'] = 1000
    case['persons']['ind1']['salary'] = 1500
    case['persons']['ind4']['salary'] = 3000
    case['persons']['ind5']['salary'] = 500

    simulation = make_simulation_from_entities(case)
    persons = simulation.persons

    salary = persons('salary', period = period)

    salary_second_parent = persons.value_from_partner(salary, persons.household, PARENT)

    assert_near(salary_second_parent, [1500, 1000, 0, 0, 0, 0])


def test_value_from_first_person(make_simulation_from_entities, case, period):
    case['persons']['ind0']['salary'] = 1000
    case['persons']['ind1']['salary'] = 1500
    case['persons']['ind4']['salary'] = 3000
    case['persons']['ind5']['salary'] = 500

    simulation = make_simulation_from_entities(case)
    household = simulation.household

    salaries = household.members('salary', period = period)
    salary_first_person = household.value_from_first_person(salaries)

    assert_near(salary_first_person, [1000, 3000])


def test_projectors_methods(simulation_couple):
    household = simulation_couple.household
    person = simulation_couple.person

    projected_vector = household.first_parent.has_role(Household.FIRST_PARENT)
    assert(len(projected_vector) == 1)  # Must be of a household dimension

    salary_i = person.household.members('salary', '2017-01')
    assert(len(person.household.sum(salary_i)) == 2)  # Must be of a person dimension
    assert(len(person.household.max(salary_i)) == 2)  # Must be of a person dimension
    assert(len(person.household.min(salary_i)) == 2)  # Must be of a person dimension
    assert(len(person.household.all(salary_i)) == 2)  # Must be of a person dimension
    assert(len(person.household.any(salary_i)) == 2)  # Must be of a person dimension
    assert(len(household.first_parent.get_rank(household, salary_i)) == 1)  # Must be of a person dimension


def test_sum_following_bug_ipp_1(make_simulation_from_entities, period):
    new_case = {
        'persons': {'ind0': {}, 'ind1': {}, 'ind2': {}, 'ind3': {}},
        'households': {
            'h1': {'parents': ['ind0']},
            'h2': {'parents': ['ind1'], 'children': ['ind2', 'ind3']}
            },
        }
    new_case['persons']['ind0']['salary'] = 2000
    new_case['persons']['ind1']['salary'] = 2000
    new_case['persons']['ind2']['salary'] = 1000
    new_case['persons']['ind3']['salary'] = 1000

    simulation = make_simulation_from_entities(new_case)
    household = simulation.household

    eligible_i = household.members('salary', period = period) < 1500
    nb_eligibles_by_household = household.sum(eligible_i, role = CHILD)

    assert_near(nb_eligibles_by_household, [0, 2])


def test_sum_following_bug_ipp_2(make_simulation_from_entities, period):
    new_case = {
        'persons': {'ind0': {}, 'ind1': {}, 'ind2': {}, 'ind3': {}},
        'households': {
            'h1': {'parents': ['ind1'], 'children': ['ind2', 'ind3']},
            'h2': {'parents': ['ind0']},
            },
        }
    new_case['persons']['ind0']['salary'] = 2000
    new_case['persons']['ind1']['salary'] = 2000
    new_case['persons']['ind2']['salary'] = 1000
    new_case['persons']['ind3']['salary'] = 1000

    simulation = make_simulation_from_entities(new_case)
    household = simulation.household

    eligible_i = household.members('salary', period = period) < 1500
    nb_eligibles_by_household = household.sum(eligible_i, role = CHILD)

    assert_near(nb_eligibles_by_household, [2, 0])


def test_get_memory_usage(tax_benefit_system, single):
    single["persons"]["Alicia"]["salary"] = {"2017-01": 0}
    simulation = simulation_builder.build_from_dict(tax_benefit_system, single)
    simulation.calculate('disposable_income', '2017-01')
    memory_usage = simulation.person.get_memory_usage(variables = ['salary'])
    assert(memory_usage['total_nb_bytes'] > 0)
    assert(len(memory_usage['by_variable']) == 1)


def test_unordered_persons(make_simulation_from_entities, period):
    new_case = {
        'persons': {'ind4': {}, 'ind3': {}, 'ind1': {}, 'ind2': {}, 'ind5': {}, 'ind0': {}},
        'households': {
            'h1': {'children': ['ind2', 'ind3'], 'parents': ['ind0', 'ind1']},
            'h2': {'children': ['ind5'], 'parents': ['ind4']}
            },
        }
    # 1st family
    new_case['persons']['ind0']['salary'] = 1000
    new_case['persons']['ind1']['salary'] = 1500
    new_case['persons']['ind2']['salary'] = 20
    new_case['households']['h1']['accommodation_size'] = 160

    # 2nd family
    new_case['persons']['ind4']['salary'] = 3000
    new_case['persons']['ind5']['salary'] = 500
    new_case['households']['h2']['accommodation_size'] = 60

    # household.members_entity_id == [1, 0, 0, 0, 1, 0]

    simulation = make_simulation_from_entities(new_case, period)
    household = simulation.household
    person = simulation.person

    salary = household.members('salary', "2016-01")  # [ 3000, 0, 1500, 20, 500, 1000 ]
    accommodation_size = household('accommodation_size', "2016-01")  # [ 160, 60 ]

    # Aggregation/Projection persons -> entity

    assert_near(household.sum(salary), [2520, 3500])
    assert_near(household.max(salary), [1500, 3000])
    assert_near(household.min(salary), [0, 500])
    assert_near(household.all(salary > 0), [False, True])
    assert_near(household.any(salary > 2000), [False, True])
    assert_near(household.first_person('salary', "2016-01"), [0, 3000])
    assert_near(household.first_parent('salary', "2016-01"), [1000, 3000])
    assert_near(household.second_parent('salary', "2016-01"), [1500, 0])
    assert_near(person.value_from_partner(salary, person.household, PARENT), [0, 0, 1000, 0, 0, 1500])

    assert_near(household.sum(salary, role = PARENT), [2500, 3000])
    assert_near(household.sum(salary, role = CHILD), [20, 500])
    assert_near(household.max(salary, role = PARENT), [1500, 3000])
    assert_near(household.max(salary, role = CHILD), [20, 500])
    assert_near(household.min(salary, role = PARENT), [1000, 3000])
    assert_near(household.min(salary, role = CHILD), [0, 500])
    assert_near(household.all(salary > 0, role = PARENT), [True, True])
    assert_near(household.all(salary > 0, role = CHILD), [False, True])
    assert_near(household.any(salary < 1500, role = PARENT), [True, False])
    assert_near(household.any(salary > 200, role = CHILD), [False, True])

    # nb_persons

    assert_near(household.nb_persons(), [4, 2])
    assert_near(household.nb_persons(role = PARENT), [2, 1])
    assert_near(household.nb_persons(role = CHILD), [2, 1])

    # Projection entity -> persons

    assert_near(household.project(accommodation_size), [60, 160, 160, 160, 60, 160])
    assert_near(household.project(accommodation_size, role = PARENT), [60, 0, 160, 0, 0, 160])
    assert_near(household.project(accommodation_size, role = CHILD), [0, 160, 0, 160, 60, 0])
