import numpy
import pytest

from openfisca_core.entities import Entity
from openfisca_core.indexed_enums import Enum
from openfisca_core.periods import DateUnit
from openfisca_core.simulations.simulation_builder import SimulationBuilder
from openfisca_core.taxbenefitsystems import TaxBenefitSystem
from openfisca_core.variables import Variable


@pytest.fixture
def selfreferencing_entities():
    person = Entity(
        key="person",
        plural="people",
        label="A person"
    )

    person.add_relationship(person,[{
        "key": "relative",
        "max": 1
        }])

    return [person]


def test_self_relative(selfreferencing_entities) -> None:
    system = TaxBenefitSystem(selfreferencing_entities)
    simulation = SimulationBuilder().build_from_dict(
        system,
        {
            "people": {"person1": {
                "relative": "person1",
            }, "person2": {
                "relative": "person2",
            }, "person3": {
                "relative": "person3",
            }},
        },
    )

    [person] = selfreferencing_entities
    assert simulation.person.count == 3


@pytest.mark.skip(reason="TODO")
def test_has_no_role(selfreferencing_entities) -> None:
    system = TaxBenefitSystem(selfreferencing_entities)
    simulation = SimulationBuilder().build_from_dict(
        system,
        {
            "people": {"person1": {}, "person2": {}, "person3": {}},
        },
    )

    [person] = selfreferencing_entities
    assert simulation.person.count == 3


@pytest.mark.skip(reason="TODO")
def test_missing_role(selfreferencing_entities) -> None:
    system = TaxBenefitSystem(selfreferencing_entities)
    simulation = SimulationBuilder().build_from_dict(
        system,
        {
            "people": {"child": {
                "relative": "parent",
            }, "parent": {
                "relative": "greatparent",
            }, "greatparent": {}},
        },
    )

    [person] = selfreferencing_entities
    assert simulation.person.count == 3
