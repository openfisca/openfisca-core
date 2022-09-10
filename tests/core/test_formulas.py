import numpy
from pytest import fixture, approx

from openfisca_country_template import entities

from openfisca_core import commons, periods
from openfisca_core.simulations import SimulationBuilder
from openfisca_core.variables import Variable


class choice(Variable):
    value_type = int
    entity = entities.Person
    definition_period = periods.MONTH


class uses_multiplication(Variable):
    value_type = int
    entity = entities.Person
    label = 'Variable with formula that uses multiplication'
    definition_period = periods.MONTH

    def formula(person, period):
        choice = person('choice', period)
        result = (choice == 1) * 80 + (choice == 2) * 90
        return result


class returns_scalar(Variable):
    value_type = int
    entity = entities.Person
    label = 'Variable with formula that returns a scalar value'
    definition_period = periods.MONTH

    def formula(person, _period):  # pylint: disable=no-self-use
        return 666


class uses_switch(Variable):
    value_type = int
    entity = entities.Person
    label = 'Variable with formula that uses switch'
    definition_period = periods.MONTH

    def formula(person, period):
        choice = person('choice', period)
        result = commons.switch(
            choice,
            {
                1: 80,
                2: 90,
                },
            )
        return result


@fixture(scope = "module", autouse = True)
def add_variables_to_tax_benefit_system(tax_benefit_system):
    tax_benefit_system.add_variables(choice, uses_multiplication, uses_switch, returns_scalar)


@fixture
def month():
    return '2013-01'


@fixture
def simulation(tax_benefit_system, month):
    simulation_builder = SimulationBuilder()
    simulation_builder.default_period = month
    simulation = simulation_builder.build_from_variables(tax_benefit_system, {'choice': numpy.random.randint(2, size = 1000) + 1})
    simulation.debug = True
    return simulation


def test_switch(simulation, month):
    uses_switch = simulation.calculate('uses_switch', period = month)
    assert isinstance(uses_switch, numpy.ndarray)


def test_multiplication(simulation, month):
    uses_multiplication = simulation.calculate('uses_multiplication', period = month)
    assert isinstance(uses_multiplication, numpy.ndarray)


def test_broadcast_scalar(simulation, month):
    array_value = simulation.calculate('returns_scalar', period = month)
    assert isinstance(array_value, numpy.ndarray)
    assert array_value == approx(numpy.repeat(666, 1000))


def test_compare_multiplication_and_switch(simulation, month):
    uses_multiplication = simulation.calculate('uses_multiplication', period = month)
    uses_switch = simulation.calculate('uses_switch', period = month)
    assert numpy.all(uses_switch == uses_multiplication)


def test_group_encapsulation():
    """Projects a calculation to all members of an entity.

    When a household contains more than one family
    Variables can be defined for the the household
    And calculations are projected to all the member families.

    """
    from openfisca_core.taxbenefitsystems import TaxBenefitSystem
    from openfisca_core.entities import build_entity
    from openfisca_core.periods import ETERNITY

    person_entity = build_entity(
        key="person",
        plural="people",
        label="A person",
        is_person=True,
        )
    family_entity = build_entity(
        key="family",
        plural="families",
        label="A family (all members in the same household)",
        containing_entities=["household"],
        roles=[{
            "key": "member",
            "plural": "members",
            "label": "Member",
            }]
        )
    household_entity = build_entity(
        key="household",
        plural="households",
        label="A household, containing one or more families",
        roles=[{
            "key": "member",
            "plural": "members",
            "label": "Member",
            }]
        )

    entities = [person_entity, family_entity, household_entity]

    system = TaxBenefitSystem(entities)

    class household_level_variable(Variable):
        value_type = int
        entity = household_entity
        definition_period = ETERNITY

    class projected_family_level_variable(Variable):
        value_type = int
        entity = family_entity
        definition_period = ETERNITY

        def formula(family, period):
            return family.household("household_level_variable", period)

    system.add_variables(household_level_variable, projected_family_level_variable)

    simulation = SimulationBuilder().build_from_dict(system, {
        "people": {
            "person1": {},
            "person2": {},
            "person3": {}
            },
        "families": {
            "family1": {
                "members": ["person1", "person2"]
                },
            "family2": {
                "members": ["person3"]
                },
            },
        "households": {
            "household1": {
                "members": ["person1", "person2", "person3"],
                "household_level_variable": {
                    "eternity": 5
                    }
                }
            }
        })

    assert (simulation.calculate("projected_family_level_variable", "2021-01-01") == 5).all()
