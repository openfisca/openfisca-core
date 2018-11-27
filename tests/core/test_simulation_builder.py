from yaml import load
from pytest import raises

from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_core.tools import assert_near
from openfisca_country_template.entities import Household

from .test_countries import tax_benefit_system


simulation_builder = SimulationBuilder(tax_benefit_system)


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
        {'persons': {'Javier': {}}, 'household': {'parents': ['Alicia']}}
        ) == {'persons': {'Javier': {}}, 'households': {'household': {'parents': ['Alicia']}}}
