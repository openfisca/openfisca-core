import numpy
from pytest import fixture

from openfisca_core import parameters, periods, taxscales, tools


@fixture
def data():
    return {
        "description": "Social security contribution tax scale",
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
            }
        ],
    }


def test_calc():
    tax_base = numpy.array([1, 8, 10])
    tax_scale = taxscales.SingleAmountTaxScale()
    tax_scale.add_bracket(6, 0.23)
    tax_scale.add_bracket(9, 0.29)

    result = tax_scale.calc(tax_base)

    tools.assert_near(result, [0, 0.23, 0.29])


def test_to_dict():
    tax_scale = taxscales.SingleAmountTaxScale()
    tax_scale.add_bracket(6, 0.23)
    tax_scale.add_bracket(9, 0.29)

    result = tax_scale.to_dict()

    assert result == {"6": 0.23, "9": 0.29}


# TODO: move, as we're testing Scale, not SingleAmountTaxScale
def test_assign_thresholds_on_creation(data):
    scale = parameters.Scale("amount_scale", data, "")
    first_jan = periods.Instant((2017, 11, 1))
    scale_at_instant = scale.get_at_instant(first_jan)

    result = scale_at_instant.thresholds

    assert result == [0.23]


# TODO: move, as we're testing Scale, not SingleAmountTaxScale
def test_assign_amounts_on_creation(data):
    scale = parameters.Scale("amount_scale", data, "")
    first_jan = periods.Instant((2017, 11, 1))
    scale_at_instant = scale.get_at_instant(first_jan)

    result = scale_at_instant.amounts

    assert result == [6]


# TODO: move, as we're testing Scale, not SingleAmountTaxScale
def test_dispatch_scale_type_on_creation(data):
    scale = parameters.Scale("amount_scale", data, "")
    first_jan = periods.Instant((2017, 11, 1))

    result = scale.get_at_instant(first_jan)

    assert isinstance(result, taxscales.SingleAmountTaxScale)


def test_to_average__linear_interpolation():
    tax_base_on_thresholds = numpy.array([0, 2, 4, 6, 8, 10])
    tax_base_between_thresholds = numpy.array([1, 3, 5, 6.0005, 7, 9.5])

    tax_scale = taxscales.SingleAmountTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(2, 10)
    tax_scale.add_bracket(4, 30)
    tax_scale.add_bracket(6, 60)
    tax_scale.add_bracket(8, 100)
    tax_scale.add_bracket(10, 40)
    tax_scale.add_bracket(10.000000001, 0)

    result = tax_scale.to_average()

    on_thresholds_result = result.calc(tax_base_on_thresholds)
    tools.assert_near(
        on_thresholds_result,
        [0, 10, 30, 60, 100, 40],
        absolute_error_margin = 1e-10,
        )

    between_thresholds_result = result.calc(tax_base_between_thresholds)
    tools.assert_near(
        between_thresholds_result,
        [5, 20, 45, 61, 80, 55],
        absolute_error_margin = 1e-10,
        )