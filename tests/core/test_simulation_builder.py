# -*- coding: utf-8 -*-

from collections import OrderedDict

from pytest import raises, fixture

from openfisca_core.simulation_builder import SimulationBuilder, Simulation
from openfisca_core.tools import assert_near
from openfisca_core.tools.test_runner import yaml
from openfisca_country_template.entities import Household
from openfisca_country_template.situation_examples import couple

from .test_countries import tax_benefit_system


@fixture
def simulation_builder():
    return SimulationBuilder()


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


def test_hydrate_person_entity(simulation_builder):
    persons = Simulation(tax_benefit_system).persons
    persons_json = OrderedDict([('Alicia', {'salary': {}}), ('Javier', {})])  # We need an OrderedDict in Python 2
    simulation_builder.hydrate_entity(persons, persons_json)
    assert persons.count == 2
    assert persons.ids == ['Alicia', 'Javier']


def test_hydrate_person_entity_with_variables(simulation_builder):
    persons = Simulation(tax_benefit_system).persons
    persons_json = OrderedDict([('Alicia', {'salary': {'2018-11': 3000}}), ('Javier', {})])  # We need an OrderedDict in Python 2
    simulation_builder.hydrate_entity(persons, persons_json)
    assert_near(persons.get_holder('salary').get_array('2018-11'), [3000, 0])


def test_hydrate_group_entity(simulation_builder):
    simulation = Simulation(tax_benefit_system)
    simulation_builder.hydrate_entity(simulation.persons,
        OrderedDict([('Alicia', {}), ('Javier', {}), ('Sarah', {}), ('Tom', {})]))
    simulation_builder.hydrate_entity(simulation.household, {
        'Household_1': {'parents': ['Alicia', 'Javier']},
        'Household_2': {'parents': ['Tom'], 'children': ['Sarah']},
        })
    assert_near(simulation.household.members_entity_id, [0, 0, 1, 1])
    assert_near(simulation.persons.has_role(Household.PARENT), [True, True, False, True])

def test_check_persons_to_allocate(simulation_builder):
    person_id = 'Alicia'
    entity_id = 'famille1'
    role_id = 'parents'
    persons_to_allocate = ['Alicia']
    index = 0
    entity_plural = 'familles'
    persons_ids = ['Alicia']
    persons_plural = 'individus'
    simulation_builder.check_persons_to_allocate(persons_plural, entity_plural,
                                                 persons_ids,  
                                                 person_id, entity_id, role_id, 
                                                 persons_to_allocate, index)

# Test Intégration


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
