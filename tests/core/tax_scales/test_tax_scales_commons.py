from openfisca_core import parameters
from openfisca_core import taxscales
from openfisca_core import tools

import pytest


@pytest.fixture
def node():
    return parameters.ParameterNode(
        "baremes",
        data={
            "health": {
                "brackets": [
                    {"rate": {"2015-01-01": 0.05}, "threshold": {"2015-01-01": 0}},
                    {"rate": {"2015-01-01": 0.10}, "threshold": {"2015-01-01": 2000}},
                ]
            },
            "retirement": {
                "brackets": [
                    {"rate": {"2015-01-01": 0.02}, "threshold": {"2015-01-01": 0}},
                    {"rate": {"2015-01-01": 0.04}, "threshold": {"2015-01-01": 3000}},
                ]
            },
        },
    )(2015)


def test_combine_tax_scales(node):
    result = taxscales.combine_tax_scales(node)

    tools.assert_near(result.thresholds, [0, 2000, 3000])
    tools.assert_near(result.rates, [0.07, 0.12, 0.14], 1e-13)
