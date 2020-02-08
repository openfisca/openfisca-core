import numpy

from openfisca_core import taxscales
from openfisca_core import tools

import pytest


def test_bracket_indices():
    tax_base = numpy.array([0, 1, 2, 3, 4, 5])
    tax_scale = taxscales.LinearAverageRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(2, 0)
    tax_scale.add_bracket(4, 0)

    result = tax_scale.bracket_indices(tax_base)

    tools.assert_near(result, [0, 0, 0, 1, 1, 2])


def test_bracket_indices_with_factor():
    tax_base = numpy.array([0, 1, 2, 3, 4, 5])
    tax_scale = taxscales.LinearAverageRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(2, 0)
    tax_scale.add_bracket(4, 0)

    result = tax_scale.bracket_indices(tax_base, factor = 2.0)

    tools.assert_near(result, [0, 0, 0, 0, 1, 1])


def test_bracket_indices_with_round_decimals():
    tax_base = numpy.array([0, 1, 2, 3, 4, 5])
    tax_scale = taxscales.LinearAverageRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(2, 0)
    tax_scale.add_bracket(4, 0)

    result = tax_scale.bracket_indices(tax_base, round_decimals = 0)

    tools.assert_near(result, [0, 0, 1, 1, 2, 2])


def test_bracket_indices_without_tax_base():
    tax_base = numpy.array([])
    tax_scale = taxscales.LinearAverageRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(2, 0)
    tax_scale.add_bracket(4, 0)

    with pytest.raises(taxscales.EmptyArgumentError):
        tax_scale.bracket_indices(tax_base)


def test_bracket_indices_without_brackets():
    tax_base = numpy.array([0, 1, 2, 3, 4, 5])
    tax_scale = taxscales.LinearAverageRateTaxScale()

    with pytest.raises(taxscales.EmptyArgumentError):
        tax_scale.bracket_indices(tax_base)


def test_to_dict():
    tax_scale = taxscales.LinearAverageRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(100, 0.1)

    result = tax_scale.to_dict()

    assert result == {"0": 0.0, "100": 0.1}


def test_calc():
    tax_base = numpy.array([1, 1.5, 2, 2.5, 3.0, 4.0])
    tax_scale = taxscales.MarginalRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(1, 0.1)
    tax_scale.add_bracket(2, 0.2)
    tax_scale.add_bracket(3, 0)

    result = tax_scale.calc(tax_base)

    tools.assert_near(
        result,
        [0, 0.05, 0.1, 0.2, 0.3, 0.3],
        absolute_error_margin = 1e-10,
        )


def test_calc_without_round():
    tax_base = numpy.array([200, 200.2, 200.002, 200.6, 200.006, 200.5, 200.005])
    tax_scale = taxscales.MarginalRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(100, 0.1)

    result = tax_scale.calc(tax_base)

    tools.assert_near(
        result,
        [10, 10.02, 10.0002, 10.06, 10.0006, 10.05, 10.0005],
        absolute_error_margin = 1e-10,
        )


def test_calc_when_round_is_1():
    tax_base = numpy.array([200, 200.2, 200.002, 200.6, 200.006, 200.5, 200.005])
    tax_scale = taxscales.MarginalRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(100, 0.1)

    result = tax_scale.calc(tax_base, round_base_decimals = 1)

    tools.assert_near(
        result,
        [10, 10.0, 10.0, 10.1, 10.0, 10, 10.0],
        absolute_error_margin = 1e-10,
        )


def test_calc_when_round_is_2():
    tax_base = numpy.array([200, 200.2, 200.002, 200.6, 200.006, 200.5, 200.005])
    tax_scale = taxscales.MarginalRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(100, 0.1)

    result = tax_scale.calc(tax_base, round_base_decimals = 2)

    tools.assert_near(
        result,
        [10, 10.02, 10.0, 10.06, 10.00, 10.05, 10],
        absolute_error_margin = 1e-10,
        )


def test_calc_when_round_is_3():
    tax_base = numpy.array([200, 200.2, 200.002, 200.6, 200.006, 200.5, 200.005])
    tax_scale = taxscales.MarginalRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(100, 0.1)

    result = tax_scale.calc(tax_base, round_base_decimals = 3)

    tools.assert_near(
        result,
        [10, 10.02, 10.0, 10.06, 10.001, 10.05, 10],
        absolute_error_margin = 1e-10,
        )


def test_marginal_rates():
    tax_base = numpy.array([0, 10, 50, 125, 250])
    tax_scale = taxscales.MarginalRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(100, 0.1)
    tax_scale.add_bracket(200, 0.2)

    result = tax_scale.marginal_rates(tax_base)

    tools.assert_near(result, [0, 0, 0, 0.1, 0.2])


def test_inverse():
    gross_tax_base = numpy.array([1, 2, 3, 4, 5, 6])
    tax_scale = taxscales.MarginalRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(1, 0)
    tax_scale.add_bracket(3, 0)
    net_tax_base = gross_tax_base - tax_scale.calc(gross_tax_base)

    result = tax_scale.inverse()

    tools.assert_near(result.calc(net_tax_base), gross_tax_base, 1e-15)


def test_scale_tax_scales():
    tax_base = numpy.array([1, 2, 3])
    tax_base_scale = 12.345
    scaled_tax_base = tax_base * tax_base_scale
    tax_scale = taxscales.MarginalRateTaxScale()
    tax_scale.add_bracket(1, 0)
    tax_scale.add_bracket(2, 0)
    tax_scale.add_bracket(3, 0)

    result = tax_scale.scale_tax_scales(tax_base_scale)

    tools.assert_near(result.thresholds, scaled_tax_base)


def test_inverse_scaled_marginal_tax_scales():
    gross_tax_base = numpy.array([1, 2, 3, 4, 5, 6])
    gross_tax_base_scale = 12.345
    scaled_gross_tax_base = gross_tax_base * gross_tax_base_scale
    tax_scale = taxscales.MarginalRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(1, 0.1)
    tax_scale.add_bracket(3, 0.05)
    scaled_tax_scale = tax_scale.scale_tax_scales(gross_tax_base_scale)
    scaled_net_tax_base = (
        + scaled_gross_tax_base
        - scaled_tax_scale.calc(scaled_gross_tax_base)
        )

    result = scaled_tax_scale.inverse()

    tools.assert_near(result.calc(scaled_net_tax_base), scaled_gross_tax_base, 1e-13)


def test_to_average():
    tax_base = numpy.array([1, 1.5, 2, 2.5])
    tax_scale = taxscales.MarginalRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(1, 0.1)
    tax_scale.add_bracket(2, 0.2)

    result = tax_scale.to_average()

    # Note: assert_near doesn't work for inf.
    assert result.thresholds == [0, 1, 2, numpy.inf]
    assert result.rates, [0, 0, 0.05, 0.2]
    tools.assert_near(
        result.calc(tax_base),
        [0, 0.0375, 0.1, 0.125],
        absolute_error_margin = 1e-10,
        )
