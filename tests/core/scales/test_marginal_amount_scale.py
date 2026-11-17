from numpy import array
from pytest import fixture

from openfisca_core import parameters, periods, scales, tools


@fixture
def data():
    return {
        "description": "Social security contribution scale",
        "metadata": {"threshold_unit": "currency-EUR", "rate_unit": "/1"},
        "brackets": [
            {
                "threshold": {"2017-10-01": {"value": 0.23}},
                "amount": {
                    "2017-10-01": {"value": 6},
                },
            },
        ],
    }


def test_calc() -> None:
    base = array([1, 8, 10])
    scale = scales.MarginalAmountScale()
    scale.add_bracket(6, 0.23)
    scale.add_bracket(9, 0.29)

    result = scale.calc(base)

    tools.assert_near(result, [0, 0.23, 0.52])


# TODO: move, as we're testing Scale, not MarginalAmountScale
def test_dispatch_scale_type_on_creation(data) -> None:
    scale = parameters.Scale("amount_scale", data, "")
    first_jan = periods.Instant((2017, 11, 1))

    result = scale.get_at_instant(first_jan)

    assert isinstance(result, scales.MarginalAmountScale)
