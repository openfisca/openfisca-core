# -*- coding: utf-8 -*-

from typing import Iterable

from enum import Enum
from datetime import date

from pytest import raises, fixture, approx

from openfisca_core.simulation_builder import SimulationBuilder, Simulation
from openfisca_core.tools import assert_near
from openfisca_core.tools.test_runner import yaml
from openfisca_core.entities import PersonEntity, GroupEntity, build_entity
from openfisca_core.variables import Variable
from openfisca_country_template.entities import Household
from openfisca_country_template.situation_examples import couple
from openfisca_core.errors import SituationParsingError
from openfisca_core.periods import ETERNITY
from openfisca_core.indexed_enums import Enum as OFEnum


from .test_countries import tax_benefit_system


class TestVariable(Variable):
    definition_period = ETERNITY
    value_type = float

    def __init__(self, entity):
        self.__class__.entity = entity
        super().__init__()


@fixture
def simulation_builder():
    return SimulationBuilder()


@fixture
def int_variable(persons):

    class intvar(Variable):
        definition_period = ETERNITY
        value_type = int
        entity = persons.__class__

        def __init__(self):
            super().__init__()

    return intvar()


@fixture
def date_variable(persons):

    class datevar(Variable):
        definition_period = ETERNITY
        value_type = date
        entity = persons.__class__

        def __init__(self):
            super().__init__()

    return datevar()


@fixture
def enum_variable():

    class TestEnum(Variable):
        definition_period = ETERNITY
        value_type = OFEnum
        dtype = 'O'
        default_value = '0'
        is_neutralized = False
        set_input = None
        possible_values = Enum('foo', 'bar')
        name = "enum"

        def __init__(self):
            pass

    return TestEnum()


@fixture
def persons():
    class TestPersonEntity(PersonEntity):
        def __init__(self):
            super().__init__(None)
            self.plural = "persons"

        def get_variable(self, variable_name):
            result = TestVariable(TestPersonEntity)
            result.name = variable_name
            return result

        def check_variable_defined_for_entity(self, variable_name):
            return True

    return TestPersonEntity()


@fixture
def group_entity():
    class Household(GroupEntity):
        def __init__(self):
            super().__init__(None)

        def get_variable(self, variable_name):
            result = TestVariable(Household)
            result.name = variable_name
            return result

        def check_variable_defined_for_entity(self, variable_name):
            return True

    roles = [{
        'key': 'parent',
        'plural': 'parents',
        'max': 2
        }, {
        'key': 'child',
        'plural': 'children'
        }]

    entity_class = build_entity("household", "households", "", doc = "", roles = roles, is_person = False, class_override = Household)
    return entity_class()


def test_build_default_simulation(simulation_builder):
    one_person_simulation = simulation_builder.build_default_simulation(tax_benefit_system, 1)
    assert one_person_simulation.persons.count == 1
    assert one_person_simulation.household.count == 1
    assert one_person_simulation.household.members_entity_id == [0]
    assert one_person_simulation.household.members_role == Household.FIRST_PARENT

    several_persons_simulation = simulation_builder.build_default_simulation(tax_benefit_system, 4)
    assert several_persons_simulation.persons.count == 4
    assert several_persons_simulation.household.count == 4
    assert (several_persons_simulation.household.members_entity_id == [0, 1, 2, 3]).all()
    assert (several_persons_simulation.household.members_role == Household.FIRST_PARENT).all()


def test_explicit_singular_entities(simulation_builder):
    assert simulation_builder.explicit_singular_entities(
        tax_benefit_system,
        {'persons': {'Javier': {}}, 'household': {'parents': ['Javier']}}
        ) == {'persons': {'Javier': {}}, 'households': {'household': {'parents': ['Javier']}}}


def test_add_person_entity(simulation_builder, persons):
    persons_json = {'Alicia': {'salary': {}}, 'Javier': {}}
    simulation_builder.add_person_entity(persons, persons_json)
    assert simulation_builder.get_count('persons') == 2
    assert simulation_builder.get_ids('persons') == ['Alicia', 'Javier']


def test_numeric_ids(simulation_builder, persons):
    persons_json = {1: {'salary': {}}, 2: {}}
    simulation_builder.add_person_entity(persons, persons_json)
    assert simulation_builder.get_count('persons') == 2
    assert simulation_builder.get_ids('persons') == ['1', '2']


def test_add_person_entity_with_values(simulation_builder, persons):
    persons_json = {'Alicia': {'salary': {'2018-11': 3000}}, 'Javier': {}}
    simulation_builder.add_person_entity(persons, persons_json)
    assert_near(simulation_builder.get_input('salary', '2018-11'), [3000, 0])


def test_add_person_values_with_default_period(simulation_builder, persons):
    simulation_builder.set_default_period('2018-11')
    persons_json = {'Alicia': {'salary': 3000}, 'Javier': {}}
    simulation_builder.add_person_entity(persons, persons_json)
    assert_near(simulation_builder.get_input('salary', '2018-11'), [3000, 0])


def test_add_person_values_with_default_period_old_syntax(simulation_builder, persons):
    simulation_builder.set_default_period('month:2018-11')
    persons_json = {'Alicia': {'salary': 3000}, 'Javier': {}}
    simulation_builder.add_person_entity(persons, persons_json)
    assert_near(simulation_builder.get_input('salary', '2018-11'), [3000, 0])


def test_add_group_entity(simulation_builder, group_entity):
    simulation_builder.add_group_entity('persons', ['Alicia', 'Javier', 'Sarah', 'Tom'], group_entity, {
        'Household_1': {'parents': ['Alicia', 'Javier']},
        'Household_2': {'parents': ['Tom'], 'children': ['Sarah']},
        })
    assert simulation_builder.get_count('households') == 2
    assert simulation_builder.get_ids('households') == ['Household_1', 'Household_2']
    assert simulation_builder.get_memberships('households') == [0, 0, 1, 1]
    assert [role.key for role in simulation_builder.get_roles('households')] == ['parent', 'parent', 'child', 'parent']


def test_add_group_entity_loose_syntax(simulation_builder, group_entity):
    simulation_builder.add_group_entity('persons', ['Alicia', 'Javier', 'Sarah', '1'], group_entity, {
        'Household_1': {'parents': ['Alicia', 'Javier']},
        'Household_2': {'parents': 1, 'children': 'Sarah'},
        })
    assert simulation_builder.get_count('households') == 2
    assert simulation_builder.get_ids('households') == ['Household_1', 'Household_2']
    assert simulation_builder.get_memberships('households') == [0, 0, 1, 1]
    assert [role.key for role in simulation_builder.get_roles('households')] == ['parent', 'parent', 'child', 'parent']


def test_add_variable_value(simulation_builder, persons):
    salary = persons.get_variable('salary')
    instance_index = 0
    simulation_builder.entity_counts['persons'] = 1
    simulation_builder.add_variable_value(persons, salary, instance_index, 'Alicia', '2018-11', 3000)
    input_array = simulation_builder.get_input('salary', '2018-11')
    assert input_array[instance_index] == approx(3000)


def test_add_variable_value_as_expression(simulation_builder, persons):
    salary = persons.get_variable('salary')
    instance_index = 0
    simulation_builder.entity_counts['persons'] = 1
    simulation_builder.add_variable_value(persons, salary, instance_index, 'Alicia', '2018-11', '3 * 1000')
    input_array = simulation_builder.get_input('salary', '2018-11')
    assert input_array[instance_index] == approx(3000)


def test_fail_on_wrong_data(simulation_builder, persons):
    salary = persons.get_variable('salary')
    instance_index = 0
    simulation_builder.entity_counts['persons'] = 1
    with raises(SituationParsingError) as excinfo:
        simulation_builder.add_variable_value(persons, salary, instance_index, 'Alicia', '2018-11', 'alicia')
    assert excinfo.value.error == {'persons': {'Alicia': {'salary': {'2018-11': "Can't deal with value: expected type number, received 'alicia'."}}}}


def test_fail_on_ill_formed_expression(simulation_builder, persons):
    salary = persons.get_variable('salary')
    instance_index = 0
    simulation_builder.entity_counts['persons'] = 1
    with raises(SituationParsingError) as excinfo:
        simulation_builder.add_variable_value(persons, salary, instance_index, 'Alicia', '2018-11', '2 * / 1000')
    assert excinfo.value.error == {'persons': {'Alicia': {'salary': {'2018-11': "I couldn't understand '2 * / 1000' as a value for 'salary'"}}}}


def test_fail_on_integer_overflow(simulation_builder, persons, int_variable):
    instance_index = 0
    simulation_builder.entity_counts['persons'] = 1
    with raises(SituationParsingError) as excinfo:
        simulation_builder.add_variable_value(persons, int_variable, instance_index, 'Alicia', '2018-11', 9223372036854775808)
    assert excinfo.value.error == {'persons': {'Alicia': {'intvar': {'2018-11': "Can't deal with value: '9223372036854775808', it's too large for type 'integer'."}}}}


def test_fail_on_date_parsing(simulation_builder, persons, date_variable):
    instance_index = 0
    simulation_builder.entity_counts['persons'] = 1
    with raises(SituationParsingError) as excinfo:
        simulation_builder.add_variable_value(persons, date_variable, instance_index, 'Alicia', '2018-11', '2019-02-30')
    assert excinfo.value.error == {'persons': {'Alicia': {'datevar': {'2018-11': "Can't deal with date: '2019-02-30'."}}}}


def test_add_unknown_enum_variable_value(simulation_builder, persons, enum_variable):
    instance_index = 0
    simulation_builder.entity_counts['persons'] = 1
    with raises(SituationParsingError):
        simulation_builder.add_variable_value(persons, enum_variable, instance_index, 'Alicia', '2018-11', 'baz')


def test_finalize_person_entity(simulation_builder, persons):
    persons_json = {'Alicia': {'salary': {'2018-11': 3000}}, 'Javier': {}}
    simulation_builder.add_person_entity(persons, persons_json)
    simulation_builder.finalize_variables_init(persons)
    assert_near(persons.get_holder('salary').get_array('2018-11'), [3000, 0])
    assert persons.count == 2
    assert persons.ids == ['Alicia', 'Javier']


def test_canonicalize_period_keys(simulation_builder, persons):
    persons_json = {'Alicia': {'salary': {'year:2018-01': 100}}}
    simulation_builder.add_person_entity(persons, persons_json)
    simulation_builder.finalize_variables_init(persons)
    assert_near(persons.get_holder('salary').get_array('2018-12'), [100])


def test_finalize_group_entity(simulation_builder):
    simulation = Simulation(tax_benefit_system)
    simulation_builder.add_group_entity('persons', ['Alicia', 'Javier', 'Sarah', 'Tom'], simulation.household, {
        'Household_1': {'parents': ['Alicia', 'Javier']},
        'Household_2': {'parents': ['Tom'], 'children': ['Sarah']},
        })
    simulation_builder.finalize_variables_init(simulation.household)
    assert_near(simulation.household.members_entity_id, [0, 0, 1, 1])
    assert_near(simulation.persons.has_role(Household.PARENT), [True, True, False, True])


def test_check_persons_to_allocate(simulation_builder):
    entity_plural = 'familles'
    persons_plural = 'individus'
    person_id = 'Alicia'
    entity_id = 'famille1'
    role_id = 'parents'
    persons_to_allocate = ['Alicia']
    persons_ids = ['Alicia']
    index = 0
    simulation_builder.check_persons_to_allocate(persons_plural, entity_plural,
                                                 persons_ids,
                                                 person_id, entity_id, role_id,
                                                 persons_to_allocate, index)


def test_allocate_undeclared_person(simulation_builder):
    entity_plural = 'familles'
    persons_plural = 'individus'
    person_id = 'Alicia'
    entity_id = 'famille1'
    role_id = 'parents'
    persons_to_allocate = ['Alicia']
    persons_ids = []
    index = 0
    with raises(SituationParsingError) as exception:
        simulation_builder.check_persons_to_allocate(
            persons_plural, entity_plural,
            persons_ids,
            person_id, entity_id, role_id,
            persons_to_allocate, index)
    assert exception.value.error == {'familles': {'famille1': {'parents': 'Unexpected value: Alicia. Alicia has been declared in famille1 parents, but has not been declared in individus.'}}}


def test_allocate_person_twice(simulation_builder):
    entity_plural = 'familles'
    persons_plural = 'individus'
    person_id = 'Alicia'
    entity_id = 'famille1'
    role_id = 'parents'
    persons_to_allocate = []
    persons_ids = ['Alicia']
    index = 0
    with raises(SituationParsingError) as exception:
        simulation_builder.check_persons_to_allocate(
            persons_plural, entity_plural,
            persons_ids,
            person_id, entity_id, role_id,
            persons_to_allocate, index)
    assert exception.value.error == {'familles': {'famille1': {'parents': 'Alicia has been declared more than once in familles'}}}


def test_one_person_without_household(simulation_builder):
    simulation_dict = {'persons': {'Alicia': {}}}
    simulation = simulation_builder.build_from_dict(tax_benefit_system, simulation_dict)
    assert simulation.household.count == 1


def test_some_person_without_household(simulation_builder):
    input_yaml = """
        persons: {'Alicia': {}, 'Bob': {}}
        household: {'parents': ['Alicia']}
    """
    simulation = simulation_builder.build_from_dict(tax_benefit_system, yaml.load(input_yaml))
    assert simulation.household.count == 2
    parents_in_households = simulation.household.nb_persons(role = simulation.household.PARENT)
    assert parents_in_households.tolist() == [1, 1]  # household member default role is first_parent


def test_nb_persons_in_group_entity(simulation_builder):
    persons_ids: Iterable = [2, 0, 1, 4, 3]
    households_ids: Iterable = ['c', 'a', 'b']
    persons_households: Iterable = ['c', 'a', 'a', 'b', 'a']

    simulation_builder.create_entities(tax_benefit_system)
    simulation_builder.declare_person_entity('person', persons_ids)
    household_instance = simulation_builder.declare_entity('household', households_ids)
    simulation_builder.join_with_persons(household_instance, persons_households, None)

    persons_in_households = simulation_builder.nb_persons('household')

    assert persons_in_households.tolist() == [1, 3, 1]


def test_nb_persons_no_role(simulation_builder):
    persons_ids: Iterable = [2, 0, 1, 4, 3]
    households_ids: Iterable = ['c', 'a', 'b']
    persons_households: Iterable = ['c', 'a', 'a', 'b', 'a']

    simulation_builder.create_entities(tax_benefit_system)
    simulation_builder.declare_person_entity('person', persons_ids)
    household_instance = simulation_builder.declare_entity('household', households_ids)

    simulation_builder.join_with_persons(household_instance, persons_households, None)
    parents_in_households = household_instance.nb_persons(role = household_instance.PARENT)

    assert parents_in_households.tolist() == [1, 3, 1]  # household member default role is first_parent


def test_nb_persons_by_role(simulation_builder):
    persons_ids: Iterable = [2, 0, 1, 4, 3]
    households_ids: Iterable = ['c', 'a', 'b']
    persons_households: Iterable = ['c', 'a', 'a', 'b', 'a']
    persons_households_roles: Iterable = ['child', 'first_parent', 'second_parent', 'first_parent', 'child']

    simulation_builder.create_entities(tax_benefit_system)
    simulation_builder.declare_person_entity('person', persons_ids)
    household_instance = simulation_builder.declare_entity('household', households_ids)

    simulation_builder.join_with_persons(
        household_instance,
        persons_households,
        persons_households_roles
        )
    parents_in_households = household_instance.nb_persons(role = household_instance.FIRST_PARENT)

    assert parents_in_households.tolist() == [0, 1, 1]


# Test Intégration


def test_from_person_variable_to_group(simulation_builder):
    persons_ids: Iterable = [2, 0, 1, 4, 3]
    households_ids: Iterable = ['c', 'a', 'b']

    persons_households: Iterable = ['c', 'a', 'a', 'b', 'a']

    persons_salaries: Iterable = [6000, 2000, 1000, 1500, 1500]
    households_rents = [1036.6667, 781.6667, 271.6667]

    period = '2018-12'

    simulation_builder.create_entities(tax_benefit_system)
    simulation_builder.declare_person_entity('person', persons_ids)

    household_instance = simulation_builder.declare_entity('household', households_ids)
    simulation_builder.join_with_persons(household_instance, persons_households, None)

    simulation = simulation_builder.build(tax_benefit_system)
    simulation.set_input('salary', period, persons_salaries)
    simulation.set_input('rent', period, households_rents)

    total_taxes = simulation.calculate('total_taxes', period)
    assert total_taxes == approx(households_rents)
    assert total_taxes / simulation.calculate('rent', period) == approx(1)


def test_simulation(simulation_builder):
    input_yaml = """
        salary:
            2016-10: 12000
    """

    simulation = simulation_builder.build_from_dict(tax_benefit_system, yaml.load(input_yaml))

    assert simulation.get_array("salary", "2016-10") == 12000
    simulation.calculate("income_tax", "2016-10")
    simulation.calculate("total_taxes", "2016-10")


def test_vectorial_input(simulation_builder):
    input_yaml = """
        salary:
            2016-10: [12000, 20000]
    """

    simulation = simulation_builder.build_from_dict(tax_benefit_system, yaml.load(input_yaml))

    assert_near(simulation.get_array("salary", "2016-10"), [12000, 20000])
    simulation.calculate("income_tax", "2016-10")
    simulation.calculate("total_taxes", "2016-10")


def test_fully_specified_entities(simulation_builder):
    simulation = simulation_builder.build_from_dict(tax_benefit_system, couple)
    assert simulation.household.count == 1
    assert simulation.persons.count == 2


def test_single_entity_shortcut(simulation_builder):
    input_yaml = """
        persons:
          Alicia: {}
          Javier: {}
        household:
          parents: [Alicia, Javier]
    """

    simulation = simulation_builder.build_from_dict(tax_benefit_system, yaml.load(input_yaml))
    assert simulation.household.count == 1


def test_order_preserved(simulation_builder):
    input_yaml = """
        persons:
          Javier: {}
          Alicia: {}
          Sarah: {}
          Tom: {}
        household:
          parents: [Alicia, Javier]
          children: [Tom, Sarah]
    """

    data = yaml.load(input_yaml)
    simulation = simulation_builder.build_from_dict(tax_benefit_system, data)

    assert simulation.persons.ids == ['Javier', 'Alicia', 'Sarah', 'Tom']


def test_inconsistent_input(simulation_builder):
    input_yaml = """
        salary:
            2016-10: [12000, 20000]
        income_tax:
            2016-10: [100, 200, 300]
    """
    with raises(ValueError) as error:
        simulation_builder.build_from_dict(tax_benefit_system, yaml.load(input_yaml))
    assert "its length is 3 while there are 2" in error.value.args[0]
