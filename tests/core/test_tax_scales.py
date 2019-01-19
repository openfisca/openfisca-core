# -*- coding: utf-8 -*-


from __future__ import unicode_literals, print_function, division, absolute_import
import numpy as np

from openfisca_core.taxscales import *
from openfisca_core.tools import assert_near
from openfisca_core.parameters import Scale
from openfisca_core.periods import Instant


def test_amount_tax_scale():
    base = np.array([1, 8, 10])
    amount_tax_scale = AmountTaxScale()
    amount_tax_scale.add_bracket(6, 0.23)
    amount_tax_scale.add_bracket(9, 0.29)

    assert_near(amount_tax_scale.calc(base), [0, 0.23, 0.52])


def test_lookup_tax_scale():
    base = np.array([1, 8, 10, 12])
    tax_scale = LookupTaxScale()
    tax_scale.add_bracket(6, 0.23)
    tax_scale.add_bracket(9, 0.29)
    tax_scale.add_bracket(11, 0)

    assert_near(tax_scale.calc(base), [0, 0.23, 0.29, 0])


def test_amount_in_scale():
    data = {'description': 'Social security contribution tax scale',
            'metadata': {'threshold_unit': 'currency-EUR', 'rate_unit': '/1'},
            'brackets': [
                {
                    'amount': {
                        '2017-10-01': {'value': 6},
                        },
                    'threshold': {
                        '2017-10-01': {'value': 0.23}
                        }
                    }
                ]
            }
    scale = Scale('amount_scale', data, '')
    first_jan = Instant((2017, 11, 1))
    scale_at_instant = scale.get_at_instant(first_jan)

    assert type(scale_at_instant) == AmountTaxScale
    assert scale_at_instant.amounts[0] == 6


def test_dispatch_scale_creation_on_type():
    data = {'description': 'Social security contribution tax scale',
            'metadata': {'type': 'lookup', 'threshold_unit': 'currency-EUR', 'rate_unit': '/1'},
            'brackets': [
                {
                    'amount': {
                        '2017-10-01': {'value': 6},
                        },
                    'threshold': {
                        '2017-10-01': {'value': 0.23}
                        }
                    }
                ]
            }
    scale = Scale('amount_scale', data, '')
    first_jan = Instant((2017, 11, 1))
    scale_at_instant = scale.get_at_instant(first_jan)

    assert type(scale_at_instant) == LookupTaxScale


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
    assert_near(marginal_tax_scale.calc(base), [0, .05, .1, .2], absolute_error_margin = 1e-16)

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


def test_inverse_marginal_tax_scale():
    marginal_tax_scale = MarginalRateTaxScale()
    marginal_tax_scale.add_bracket(0, 0)
    marginal_tax_scale.add_bracket(1, 0.1)
    marginal_tax_scale.add_bracket(3, 0.05)

    brut = np.array([1, 2, 3, 4, 5, 3.28976, 8764])
    net = brut - marginal_tax_scale.calc(brut)
    inverse = marginal_tax_scale.inverse()
    assert_near(brut, inverse.calc(net), 1e-15)

    marginal_tax_scale.add_bracket(4, 0)
    net = brut - marginal_tax_scale.calc(brut)
    inverse = marginal_tax_scale.inverse()
    assert_near(brut, inverse.calc(net), 1e-15)


def test_inverse_scaled_marginal_tax_scale():
    marginal_tax_scale = MarginalRateTaxScale()
    marginal_tax_scale.add_bracket(0, 0)
    marginal_tax_scale.add_bracket(1, 0.1)
    marginal_tax_scale.add_bracket(3, 0.05)

    brut = np.array([1, 2, 3, 4, 5, 6])
    net = brut - marginal_tax_scale.calc(brut)
    inverse = marginal_tax_scale.inverse()
    assert_near(brut, inverse.calc(net), 1e-15)

    brut = np.array([1, 2, 3, 4, 5, 6])
    brut_scale = 12.345
    brut_scaled = brut * brut_scale
    scaled_marginal_tax_scale = marginal_tax_scale.scale_tax_scales(brut_scale)
    net_scaled = (brut_scaled - scaled_marginal_tax_scale.calc(brut_scaled))
    scaled_inverse = scaled_marginal_tax_scale.inverse()
    assert_near(brut_scaled, scaled_inverse.calc(net_scaled), 1e-13)

    inverse = marginal_tax_scale.inverse()
    inversed_net = inverse.calc(net)
    net_scale = brut_scale
    inversed_net_scaled = inversed_net * net_scale
    assert_near(brut_scaled, inversed_net_scaled, 1e-13)


def test_combine_tax_scales():
    from openfisca_core.parameters import ParameterNode

    node = ParameterNode('baremes', data = {
        'health': {
            'brackets': [
                {
                    'rate': {'2015-01-01': 0.05},
                    'threshold': {'2015-01-01': 0}
                    },
                {
                    'rate': {'2015-01-01': 0.10},
                    'threshold': {'2015-01-01': 2000}
                    },
                ]},
        'retirement': {
            'brackets': [
                {
                    'rate': {'2015-01-01': 0.02},
                    'threshold': {'2015-01-01': 0}
                    },
                {
                    'rate': {'2015-01-01': 0.04},
                    'threshold': {'2015-01-01': 3000}
                    },
                ]
            },
        })(2015)

    bareme = combine_tax_scales(node)
    assert_near(bareme.thresholds, [0, 2000, 3000])
    assert_near(bareme.rates, [0.07, 0.12, 0.14], 1e-13)


if __name__ == '__main__':
    import logging
    import sys
    logging.basicConfig(level = logging.ERROR, stream = sys.stdout)
    test_inverse_marginal_tax_scale()
