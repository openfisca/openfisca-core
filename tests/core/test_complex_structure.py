import numpy

from openfisca_core.entities import Entity
from openfisca_core.indexed_enums import Enum
from openfisca_core.periods import DateUnit
from openfisca_core.simulations.simulation_builder import SimulationBuilder
from openfisca_core.taxbenefitsystems import TaxBenefitSystem
from openfisca_core.variables import Variable


def test_has_conflicting_role() -> None:
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

    entities = [person, household, family]
    system = TaxBenefitSystem(entities)
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

    assert (simulation.person.has_role(household.CHILD) == [False, True, True]).all()
    assert (simulation.person.has_role(family.CHILD) == [False, False, True]).all()
