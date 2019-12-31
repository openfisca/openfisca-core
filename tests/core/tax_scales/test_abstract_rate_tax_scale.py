from numpy import array

from openfisca_core.taxscales import AbstractRateTaxScale
from openfisca_core.tools import assert_near


def test_bracket_indices():
    tax_base = array([0, 1, 2, 3, 4, 5])
    tax_scale = AbstractRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(2, 0)
    tax_scale.add_bracket(4, 0)

    result = tax_scale.bracket_indices(tax_base)

    assert_near(result, [0, 0, 0, 1, 1, 2])


def test_bracket_indices_with_factor():
    tax_base = array([0, 1, 2, 3, 4, 5])
    tax_scale = AbstractRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(2, 0)
    tax_scale.add_bracket(4, 0)

    result = tax_scale.bracket_indices(tax_base, factor = 2.0)

    assert_near(result, [0, 0, 0, 0, 1, 1])


def test_bracket_indices_with_round_decimals():
    tax_base = array([0, 1, 2, 3, 4, 5])
    tax_scale = AbstractRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(2, 0)
    tax_scale.add_bracket(4, 0)

    result = tax_scale.bracket_indices(tax_base, round_decimals = 0)

    assert_near(result, [0, 0, 1, 1, 2, 2])


def test_bracket_indices_without_tax_base():
    tax_base = array([])
    tax_scale = AbstractRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(2, 0)
    tax_scale.add_bracket(4, 0)

    result = tax_scale.bracket_indices(tax_base)

    assert_near(result, [])


def test_bracket_indices_without_brackets():
    tax_base = array([0, 1, 2, 3, 4, 5])
    tax_scale = AbstractRateTaxScale()

    result = tax_scale.bracket_indices(tax_base)

    assert_near(result, [0, 0, 0, 0, 0, 0])


def test_to_dict():
    tax_scale = AbstractRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(100, 0.1)

    result = tax_scale.to_dict()

    assert result == {"0": 0.0, "100": 0.1}
