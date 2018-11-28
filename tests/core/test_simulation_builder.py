from yaml import load
from pytest import raises

from openfisca_core.simulation_builder import SimulationBuilder, Simulation
from openfisca_core.tools import assert_near
from openfisca_country_template.entities import Household
from openfisca_country_template.situation_examples import couple

from .test_countries import tax_benefit_system


simulation_builder = SimulationBuilder(tax_benefit_system)


# Test helpers


def test_build_default_simulation():
    one_person_simulation = simulation_builder.build_default_simulation(1)
    assert one_person_simulation.persons.count == 1
    assert one_person_simulation.household.count == 1
    assert one_person_simulation.household.members_entity_id == [0]
    assert one_person_simulation.household.members_role == Household.FIRST_PARENT

    several_persons_simulation = simulation_builder.build_default_simulation(4)
    assert several_persons_simulation.persons.count == 4
    assert several_persons_simulation.household.count == 4
    assert (several_persons_simulation.household.members_entity_id == [0, 1, 2, 3]).all()
    assert (several_persons_simulation.household.members_role == Household.FIRST_PARENT).all()


def test_explicit_singular_entities():
    assert simulation_builder.explicit_singular_entities(
        {'persons': {'Javier': {}}, 'household': {'parents': ['Javier']}}
        ) == {'persons': {'Javier': {}}, 'households': {'household': {'parents': ['Javier']}}}


def test_hydrate_person_entity():
    persons = Simulation(tax_benefit_system).persons
    simulation_builder.hydrate_entity(persons, {'Alicia': {}, 'Javier': {}})
    assert persons.count == 2
    assert persons.ids == ['Alicia', 'Javier']


def test_hydrate_person_entity_with_variables():
    persons = Simulation(tax_benefit_system).persons
    simulation_builder.hydrate_entity(persons, {'Alicia': {'salary': {'2018-11': 3000}}, 'Javier': {}})
    assert_near(persons.get_holder('salary').get_array('2018-11'), [3000, 0])


def test_hydrate_group_entity():
    simulation = Simulation(tax_benefit_system)
    simulation_builder.hydrate_entity(simulation.persons, {'Alicia': {}, 'Javier': {}, 'Sarah': {}, 'Tom': {}})
    simulation_builder.hydrate_entity(simulation.household, {
        'Household_1': {'parents': ['Alicia', 'Javier']},
        'Household_2': {'parents': ['Tom'], 'children': ['Sarah']},
        })
    assert_near(simulation.household.members_entity_id, [0, 0, 1, 1])
    assert_near(simulation.persons.has_role(Household.PARENT), [True, True, False, True])


# Test Intégration


def test_simulation():
    input_yaml = """
        salary:
            2016-10: 12000
    """

    simulation = simulation_builder.build_from_dict(load(input_yaml))

    assert simulation.get_array("salary", "2016-10") == 12000
    simulation.calculate("income_tax", "2016-10")
    simulation.calculate("total_taxes", "2016-10")


def test_vectorial_input():
    input_yaml = """
        salary:
            2016-10: [12000, 20000]
    """

    simulation = simulation_builder.build_from_dict(load(input_yaml))

    assert_near(simulation.get_array("salary", "2016-10"), [12000, 20000])
    simulation.calculate("income_tax", "2016-10")
    simulation.calculate("total_taxes", "2016-10")


def test_fully_specified_entities():
    simulation = simulation_builder.build_from_dict(couple)
    assert simulation.household.count == 1
    assert simulation.persons.count == 2


def test_single_entity_shortcut():
    input_yaml = """
        persons:
          Alicia: {}
          Javier: {}
        household:
          parents: [Alicia, Javier]
    """

    simulation = simulation_builder.build_from_dict(load(input_yaml))
    assert simulation.household.count == 1


def test_inconsistent_input():
    input_yaml = """
        salary:
            2016-10: [12000, 20000]
        income_tax:
            2016-10: [100, 200, 300]
    """
    with raises(ValueError) as error:
        simulation_builder.build_from_dict(load(input_yaml))
    assert "its length is 3 while there are 2" in error.value.args[0]
