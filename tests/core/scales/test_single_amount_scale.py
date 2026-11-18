import numpy
from pytest import fixture

from openfisca_core import parameters, periods, scales, tools


@fixture
def data():
    return {
        "description": "Social security contribution scale",
        "metadata": {
            "type": "single_amount",
            "threshold_unit": "currency-EUR",
            "rate_unit": "/1",
        },
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
    base = numpy.array([1, 8, 10])
    scale = scales.SingleAmountScale()
    scale.add_bracket(6, 0.23)
    scale.add_bracket(9, 0.29)

    result = scale.calc(base)

    tools.assert_near(result, [0, 0.23, 0.29])


def test_to_dict() -> None:
    scale = scales.SingleAmountScale()
    scale.add_bracket(6, 0.23)
    scale.add_bracket(9, 0.29)

    result = scale.to_dict()

    assert result == {"6": 0.23, "9": 0.29}


# TODO: move, as we're testing Scale, not SingleAmountScale
def test_assign_thresholds_on_creation(data) -> None:
    scale = parameters.Scale("amount_scale", data, "")
    first_jan = periods.Instant((2017, 11, 1))
    scale_at_instant = scale.get_at_instant(first_jan)

    result = scale_at_instant.thresholds

    assert result == [0.23]


# TODO: move, as we're testing Scale, not SingleAmountScale
def test_assign_amounts_on_creation(data) -> None:
    scale = parameters.Scale("amount_scale", data, "")
    first_jan = periods.Instant((2017, 11, 1))
    scale_at_instant = scale.get_at_instant(first_jan)

    result = scale_at_instant.amounts

    assert result == [6]


# TODO: move, as we're testing Scale, not SingleAmountScale
def test_dispatch_scale_type_on_creation(data) -> None:
    scale = parameters.Scale("amount_scale", data, "")
    first_jan = periods.Instant((2017, 11, 1))

    result = scale.get_at_instant(first_jan)

    assert isinstance(result, scales.SingleAmountScale)
