from numpy import array
from pytest import fixture

from openfisca_core import parameters
from openfisca_core import periods
from openfisca_core import taxscales
from openfisca_core import tools


@fixture
def data():
    return {
        "description": "Social security contribution tax scale",
        "metadata": {"threshold_unit": "currency-EUR", "rate_unit": "/1"},
        "brackets": [
            {
                "threshold": {"2017-10-01": {"value": 0.23}},
                "amount": {"2017-10-01": {"value": 6}, },
                }
            ],
        }


def test_calc():
    tax_base = array([1, 8, 10])
    tax_scale = taxscales.MarginalAmountTaxScale()
    tax_scale.add_bracket(6, 0.23)
    tax_scale.add_bracket(9, 0.29)

    result = tax_scale.calc(tax_base)

    tools.assert_near(result, [0, 0.23, 0.52])


# TODO: move, as we're testing Scale, not MarginalAmountTaxScale
def test_dispatch_scale_type_on_creation(data):
    scale = parameters.Scale("amount_scale", data, "")
    first_jan = periods.Instant((2017, 11, 1))

    result = scale.get_at_instant(first_jan)

    assert isinstance(result, taxscales.MarginalAmountTaxScale)
