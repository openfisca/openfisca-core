# -*- coding: utf-8 -*-


import numpy as np

from openfisca_core.taxscales import MarginalRateTaxScale
from openfisca_core.tools import assert_near


def test_simple_linear_average_rate_tax_scale():
    base = np.array([1, 1.5, 2, 2.5, 3.0, 4.0])

    marginal_tax_scale = MarginalRateTaxScale()
    marginal_tax_scale.add_bracket(0, 0)
    marginal_tax_scale.add_bracket(1, 0.1)
    marginal_tax_scale.add_bracket(2, 0.2)
    marginal_tax_scale.add_bracket(3, 0)
    assert_near(marginal_tax_scale.calc(base), [0, .05, .1, .2, .3, .3], absolute_error_margin = 1e-10)


def test_linear_average_rate_tax_scale():
    base = np.array([1, 1.5, 2, 2.5])

    marginal_tax_scale = MarginalRateTaxScale()
    marginal_tax_scale.add_bracket(0, 0)
    marginal_tax_scale.add_bracket(1, 0.1)
    marginal_tax_scale.add_bracket(2, 0.2)
    assert_near(marginal_tax_scale.calc(base), [0, .05, .1, .2], absolute_error_margin = 0)

    average_tax_scale = marginal_tax_scale.to_average()
    # Note: assert_near doesn't work for inf.
    # assert_near(average_tax_scale.thresholds, [0, 1, 2, np.inf], absolute_error_margin = 0)
    assert average_tax_scale.thresholds == [0, 1, 2, np.inf]
    assert_near(average_tax_scale.rates, [0, 0, 0.05, 0.2], absolute_error_margin = 0)
    assert_near(average_tax_scale.calc(base), [0, 0.0375, 0.1, 0.125], absolute_error_margin = 1e-10)

    new_marginal_tax_scale = average_tax_scale.to_marginal()
    assert_near(new_marginal_tax_scale.thresholds, marginal_tax_scale.thresholds, absolute_error_margin = 0)
    assert_near(new_marginal_tax_scale.rates, marginal_tax_scale.rates, absolute_error_margin = 0)
    assert_near(average_tax_scale.rates, [0, 0, 0.05, 0.2], absolute_error_margin = 0)


def test_round_marginal_tax_scale():

    base = np.array([200, 200.2, 200.002, 200.6, 200.006, 200.5, 200.005])

    marginal_tax_scale = MarginalRateTaxScale()
    marginal_tax_scale.add_bracket(0, 0)
    marginal_tax_scale.add_bracket(100, 0.1)

    assert_near(
        marginal_tax_scale.calc(base),
        [10, 10.02, 10.0002, 10.06, 10.0006, 10.05, 10.0005],
        absolute_error_margin = 1e-10,
        )
    assert_near(
        marginal_tax_scale.calc(base, round_base_decimals = 1),
        [10, 10., 10., 10.1, 10., 10, 10.],
        absolute_error_margin = 1e-10,
        )
    assert_near(
        marginal_tax_scale.calc(base, round_base_decimals = 2),
        [10, 10.02, 10., 10.06, 10.00, 10.05, 10],
        absolute_error_margin = 1e-10,
        )
    assert_near(
        marginal_tax_scale.calc(base, round_base_decimals = 3),
        [10, 10.02, 10., 10.06, 10.001, 10.05, 10],
        absolute_error_margin = 1e-10,
        )


if __name__ == '__main__':
    import logging
    import sys
    logging.basicConfig(level = logging.ERROR, stream = sys.stdout)
