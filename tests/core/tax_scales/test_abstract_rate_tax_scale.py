from numpy import array

from openfisca_core.taxscales import AbstractRateTaxScale
from openfisca_core.tools import assert_near


def test_bracket_indices():
    tax_base = array([0, 10, 50, 125, 250])
    tax_scale = AbstractRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(100, 0)
    tax_scale.add_bracket(200, 0)

    result = tax_scale.bracket_indices(tax_base)

    assert_near(result, [0, 0, 0, 1, 2])


def test_to_dict():
    tax_scale = AbstractRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(100, 0.1)

    result = tax_scale.to_dict()

    assert result == {"0": 0.0, "100": 0.1}
