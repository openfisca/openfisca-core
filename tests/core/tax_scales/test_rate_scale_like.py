import numpy
import pytest

from openfisca_core import tools
from openfisca_core.errors import EmptyArgumentError
from openfisca_core.taxscales import RateTaxScaleLike


class RateTaxScale(RateTaxScaleLike):

    def calc(self, __arg1, __arg2):
        ...


@pytest.fixture
def tax_base():
    return numpy.array([0, 1, 2, 3, 4, 5])


@pytest.fixture
def tax_scale():
    tax_scale = RateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(2, 0)
    tax_scale.add_bracket(4, 0)

    return tax_scale


def test_bracket_indices(tax_base, tax_scale):
    result = tax_scale.bracket_indices(tax_base)

    tools.assert_near(result, [0, 0, 0, 1, 1, 2])


def test_bracket_indices_with_factor(tax_base, tax_scale):
    result = tax_scale.bracket_indices(tax_base, factor = 2.0)

    tools.assert_near(result, [0, 0, 0, 0, 1, 1])


def test_bracket_indices_with_round_decimals(tax_base, tax_scale):
    result = tax_scale.bracket_indices(tax_base, round_decimals = 0)

    tools.assert_near(result, [0, 0, 1, 1, 2, 2])


def test_bracket_indices_without_tax_base(tax_scale):
    tax_base = numpy.array([])

    with pytest.raises(EmptyArgumentError):
        tax_scale.bracket_indices(tax_base)


def test_bracket_indices_without_brackets(tax_base):
    tax_scale = RateTaxScale()

    with pytest.raises(EmptyArgumentError):
        tax_scale.bracket_indices(tax_base)


def test_to_dict():
    tax_scale = RateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(100, 0.1)

    result = tax_scale.to_dict()

    assert result == {"0": 0.0, "100": 0.1}
