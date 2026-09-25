import numpy
import pytest

from openfisca_core.entities import Entity
from openfisca_core.indexed_enums import Enum
from openfisca_core.periods import DateUnit
from openfisca_core.simulations.simulation_builder import SimulationBuilder
from openfisca_core.taxbenefitsystems import TaxBenefitSystem
from openfisca_core.variables import Variable


@pytest.fixture
def multimembership_entities():
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
                "key": "adult",
                "plural": "adults",
                "label": "Adult",
            },
            {
                "key": "child",
                "plural": "children",
                "label": "Child",
            },
        ],
    )
    family = Entity(
        key="family",
        plural="families",
        label="A family",
    )
    family.add_relationship(person,
        [
            {
                "key": "parent",
                "plural": "parents",
                "label": "Parent",
                "subroles": ["parent1", "parent2"]
            },
            {
                "key": "child",
                "plural": "children",
                "label": "Child",
            },
        ],
    )

    return [person, household, family]


def test_has_conflicting_role(multimembership_entities) -> None:
    system = TaxBenefitSystem(multimembership_entities)
    simulation = SimulationBuilder().build_from_dict(
        system,
        {
            "people": {"person1": {}, "person2": {}, "person3": {}},
            "households": {
                "household1": {
                    "adults": ["person1"],
                    "children": ["person2", "person3"],
                },
            },
            "families": {
                "family1": {
                    "parents": ["person1", "person2"],
                    "children": ["person3"],
                },
            },
        },
    )

    [person, household, family] = multimembership_entities
    assert (simulation.person.has_role(household.CHILD) == [False, True, True]).all()
    assert (simulation.person.has_role(family.CHILD) == [False, False, True]).all()


def test_get_rank_with_multiple_memberships(multimembership_entities) -> None:
    [person, household, family] = multimembership_entities
    class person_int_variable(Variable):
        value_type = int
        entity = person
        definition_period = DateUnit.ETERNITY

    system = TaxBenefitSystem(multimembership_entities)
    system.add_variables(person_int_variable)
    simulation = SimulationBuilder().build_from_dict(
        system,
        {
            "people": {
                "person1": {
                    "person_int_variable": {"ETERNITY": 3},
                }, "person2": {
                    "person_int_variable": {"ETERNITY": 2},
                }, "person3": {
                    "person_int_variable": {"ETERNITY": 1},
                }
            },
            "households": {
                "household1": {
                    "adults": ["person1"],
                    "children": ["person2", "person3"],
                },
            },
            "families": {
                "family1": {
                    "parents": ["person1", "person2"],
                    "children": ["person3"],
                },
            },
        },
    )

    ranks = simulation.calculate("person_int_variable", "ETERNITY")
    assert (simulation.person.get_rank(simulation.family, ranks) == [2, 1, 0]).all()
