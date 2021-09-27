import numpy
import pytest

from openfisca_core import taxscales
from openfisca_core import tools


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


def test_to_marginal():
    tax_base = numpy.array([1, 1.5, 2, 2.5])
    tax_scale = taxscales.LinearAverageRateTaxScale()
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
