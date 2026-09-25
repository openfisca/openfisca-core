import numpy
import pytest

from openfisca_core.entities import Entity
from openfisca_core.indexed_enums import Enum
from openfisca_core.periods import DateUnit
from openfisca_core.simulations.simulation_builder import SimulationBuilder
from openfisca_core.taxbenefitsystems import TaxBenefitSystem
from openfisca_core.variables import Variable


@pytest.fixture
def unrelated_entities():
    person = Entity(
        key="person",
        plural="people",
        label="A person"
    )
    contract = Entity(
        key="contract",
        plural="contracts",
        label="A contract"
    )

    return [person, contract]


def test_has_conflicting_role(unrelated_entities) -> None:
    system = TaxBenefitSystem(unrelated_entities)
    simulation = SimulationBuilder().build_from_dict(
        system,
        {
            "people": {"person1": {}, "person2": {}, "person3": {}},
            "contracts": {"contract1": {}, "contract2": {}},
        },
    )

    [person, contract] = unrelated_entities
    assert simulation.person.count == 3
    assert simulation.contract.count == 2
