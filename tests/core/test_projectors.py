import numpy

from openfisca_core.entities import Entity
from openfisca_core.indexed_enums import Enum
from openfisca_core.periods import DateUnit
from openfisca_core.simulations.simulation_builder import SimulationBuilder
from openfisca_core.taxbenefitsystems import TaxBenefitSystem
from openfisca_core.variables import Variable


def test_enum_projects_downwards() -> None:
    """Test that an Enum-type household-level variable projects
    values onto its members correctly.
    """
    person = Entity(
        key="person",
        plural="people",
        label="A person"
    )
    household = Entity(
        key="household",
        plural="households",
        label="A household"
    )
    household.add_relationship(person,
        [
            {
                "key": "member",
                "plural": "members",
                "label": "Member",
            },
        ],
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
        definition_period = DateUnit.ETERNITY

    class projected_enum_variable(Variable):
        value_type = Enum
        possible_values = enum
        default_value = enum.FIRST_OPTION
        entity = person
        definition_period = DateUnit.ETERNITY

        def formula(person, period):
            return person.household("household_enum_variable", period)

    system.add_variables(household_enum_variable, projected_enum_variable)

    simulation = SimulationBuilder().build_from_dict(
        system,
        {
            "people": {"person1": {}, "person2": {}, "person3": {}},
            "households": {
                "household1": {
                    "members": ["person1", "person2", "person3"],
                    "household_enum_variable": {"eternity": "SECOND_OPTION"},
                },
            },
        },
    )

    assert (
        simulation.calculate("projected_enum_variable", "2021-01-01").decode_to_str()
        == numpy.array(["SECOND_OPTION"] * 3)
    ).all()


def test_enum_projects_upwards() -> None:
    """Test that an Enum-type person-level variable projects
    values onto its household (from the first person) correctly.
    """
    person = Entity(
        key="person",
        plural="people",
        label="A person"
    )
    household = Entity(
        key="household",
        plural="households",
        label="A household",
    )
    household.add_relationship(person,
        [
            {
                "key": "member",
                "plural": "members",
                "label": "Member",
            },
        ],
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
        definition_period = DateUnit.ETERNITY

        def formula(self, period):
            return self.value_from_first_person(
                self.members("person_enum_variable", period),
            )

    class person_enum_variable(Variable):
        value_type = Enum
        possible_values = enum
        default_value = enum.FIRST_OPTION
        entity = person
        definition_period = DateUnit.ETERNITY

    system.add_variables(household_projected_variable, person_enum_variable)

    simulation = SimulationBuilder().build_from_dict(
        system,
        {
            "people": {
                "person1": {"person_enum_variable": {"ETERNITY": "SECOND_OPTION"}},
                "person2": {},
                "person3": {},
            },
            "households": {
                "household1": {
                    "members": ["person1", "person2", "person3"],
                },
            },
        },
    )

    assert (
        simulation.calculate(
            "household_projected_variable",
            "2021-01-01",
        ).decode_to_str()
        == numpy.array(["SECOND_OPTION"])
    ).all()
