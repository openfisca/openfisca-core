import numpy

from openfisca_core import tools
from openfisca_core.taxscales import LinearAverageRateTaxScale


def test_to_marginal():
    tax_base = numpy.array([1, 1.5, 2, 2.5])
    tax_scale = LinearAverageRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(1, 0.1)
    tax_scale.add_bracket(2, 0.2)

    result = tax_scale.to_marginal()

    assert result.thresholds == [0, 1, 2]
    tools.assert_near(result.rates, [0.1, 0.3, 0.2], absolute_error_margin = 0)
    tools.assert_near(
        result.calc(tax_base),
        [0.1, 0.25, 0.4, 0.5],
        absolute_error_margin = 0,
        )
