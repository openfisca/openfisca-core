import numpy as np
from pytest import fixture

from openfisca_core.entities import build_entity
from openfisca_core.periods import DateUnit
from openfisca_core.simulations import SimulationBuilder
from openfisca_core.taxbenefitsystems import TaxBenefitSystem
from openfisca_core.variables import Variable

Person = build_entity(
    key="person",
    plural="persons",
    label="Person",
    is_person=True,
)


@fixture
def tbs():
    return TaxBenefitSystem([Person])


def test_float32_precision():
    """
    Reproduction of float precision issue.
    Calculated from: 524709269 * 0.13 = 68212204.97 -> np.round(68212204.97)

    In float64, this test will pass with a result 68212205.0
    In float32, this test will fail with a result 68212200.0
    """
    tbs = TaxBenefitSystem([Person])

    class value(Variable):
        value_type = float
        entity = Person
        definition_period = DateUnit.MONTH

    class rate(Variable):
        value_type = float
        entity = Person
        definition_period = DateUnit.MONTH
        default_value = 0.13

    class total(Variable):
        value_type = float
        entity = Person
        definition_period = DateUnit.MONTH

        def formula(person, period, parameters):
            value1 = person("value", period)
            rate1 = person("rate", period)
            return np.round(value1 * rate1)

    tbs.add_variable(value)
    tbs.add_variable(rate)
    tbs.add_variable(total)

    period = "2020-01"
    sb = SimulationBuilder()
    sim = sb.build_from_dict(tbs, {
        "persons": {
            "p1": {
                "value": {period: 524709269}
            }
        }
    })

    result = sim.calculate("total", period)
    expected = 68212205.0

    assert result[0] == expected, f"Expected {expected}, got {result[0]}"


