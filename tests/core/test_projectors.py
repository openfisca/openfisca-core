from openfisca_core.simulations.simulation_builder import SimulationBuilder
from openfisca_core.taxbenefitsystems import TaxBenefitSystem
from openfisca_core.entities import build_entity
from openfisca_core.model_api import Enum, Variable, ETERNITY
import numpy


def test_shortcut_to_containing_entity_provided():
    """
    Tests that, when an entity provides a containing entity,
    the shortcut to that containing entity is provided.
    """
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
    simulation = SimulationBuilder().build_from_dict(system, {})
    assert simulation.populations["family"].household.entity.key == "household"


def test_shortcut_to_containing_entity_not_provided():
    """
    Tests that, when an entity doesn't provide a containing
    entity, the shortcut to that containing entity is not provided.
    """
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
        containing_entities=[],
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
    simulation = SimulationBuilder().build_from_dict(system, {})
    try:
        simulation.populations["family"].household
        raise AssertionError()
    except AttributeError:
        pass


def test_enum_projects_downwards():
    """
    Test that an Enum-type household-level variable projects
    values onto its members correctly.
    """

    person = build_entity(
        key="person",
        plural="people",
        label="A person",
        is_person=True,
        )
    household = build_entity(
        key="household",
        plural="households",
        label="A household",
        roles=[{
            "key": "member",
            "plural": "members",
            "label": "Member",
            }]
        )

    entities = [person, household]

    system = TaxBenefitSystem(entities)

    class enum(Enum):
        FIRST_OPTION = "First option"
        SECOND_OPTION = "Second option"

    class household_enum_variable(Variable):
        value_type = Enum
        possible_values = enum
        default_value = enum.FIRST_OPTION
        entity = household
        definition_period = ETERNITY

    class projected_enum_variable(Variable):
        value_type = Enum
        possible_values = enum
        default_value = enum.FIRST_OPTION
        entity = person
        definition_period = ETERNITY

        def formula(person, period):
            return person.household("household_enum_variable", period)

    system.add_variables(household_enum_variable, projected_enum_variable)

    simulation = SimulationBuilder().build_from_dict(system, {
        "people": {
            "person1": {},
            "person2": {},
            "person3": {}
            },
        "households": {
            "household1": {
                "members": ["person1", "person2", "person3"],
                "household_enum_variable": {
                    "eternity": "SECOND_OPTION"
                    }
                }
            }
        })

    assert (simulation.calculate("projected_enum_variable", "2021-01-01").decode_to_str() == numpy.array(["SECOND_OPTION"] * 3)).all()


def test_enum_projects_upwards():
    """
    Test that an Enum-type person-level variable projects
    values onto its household (from the first person) correctly.
    """

    person = build_entity(
        key="person",
        plural="people",
        label="A person",
        is_person=True,
        )
    household = build_entity(
        key="household",
        plural="households",
        label="A household",
        roles=[{
            "key": "member",
            "plural": "members",
            "label": "Member",
            }]
        )

    entities = [person, household]

    system = TaxBenefitSystem(entities)

    class enum(Enum):
        FIRST_OPTION = "First option"
        SECOND_OPTION = "Second option"

    class household_projected_variable(Variable):
        value_type = Enum
        possible_values = enum
        default_value = enum.FIRST_OPTION
        entity = household
        definition_period = ETERNITY

        def formula(household, period):
            return household.value_from_first_person(household.members("person_enum_variable", period))

    class person_enum_variable(Variable):
        value_type = Enum
        possible_values = enum
        default_value = enum.FIRST_OPTION
        entity = person
        definition_period = ETERNITY

    system.add_variables(household_projected_variable, person_enum_variable)

    simulation = SimulationBuilder().build_from_dict(system, {
        "people": {
            "person1": {
                "person_enum_variable": {
                    "ETERNITY": "SECOND_OPTION"
                    }
                },
            "person2": {},
            "person3": {}
            },
        "households": {
            "household1": {
                "members": ["person1", "person2", "person3"],
                }
            }
        })

    assert (simulation.calculate("household_projected_variable", "2021-01-01").decode_to_str() == numpy.array(["SECOND_OPTION"])).all()


def test_enum_projects_between_containing_groups():
    """
    Test that an Enum-type person-level variable projects
    values onto its household (from the first person) correctly.
    """

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

    class enum(Enum):
        FIRST_OPTION = "First option"
        SECOND_OPTION = "Second option"

    class household_level_variable(Variable):
        value_type = Enum
        possible_values = enum
        default_value = enum.FIRST_OPTION
        entity = household_entity
        definition_period = ETERNITY

    class projected_family_level_variable(Variable):
        value_type = Enum
        possible_values = enum
        default_value = enum.FIRST_OPTION
        entity = family_entity
        definition_period = ETERNITY

        def formula(family, period):
            return family.household("household_level_variable", period)

    class decoded_projected_family_level_variable(Variable):
        value_type = str
        entity = family_entity
        definition_period = ETERNITY

        def formula(family, period):
            return family.household("household_level_variable", period).decode_to_str()

    system.add_variables(
        household_level_variable,
        projected_family_level_variable,
        decoded_projected_family_level_variable
        )

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
                    "eternity": "SECOND_OPTION"
                    }
                }
            }
        })

    assert (simulation.calculate("projected_family_level_variable", "2021-01-01").decode_to_str() == numpy.array(["SECOND_OPTION"])).all()
    assert (simulation.calculate("decoded_projected_family_level_variable", "2021-01-01") == numpy.array(["SECOND_OPTION"])).all()
