import numpy
import pytest

from openfisca_core import scales, tools


def test_bracket_indices() -> None:
    base = numpy.array([0, 1, 2, 3, 4, 5])
    scale = scales.AverageRateScale()
    scale.add_bracket(0, 0)
    scale.add_bracket(2, 0)
    scale.add_bracket(4, 0)

    result = scale.bracket_indices(base)

    tools.assert_near(result, [0, 0, 0, 1, 1, 2])


def test_bracket_indices_with_factor() -> None:
    base = numpy.array([0, 1, 2, 3, 4, 5])
    scale = scales.AverageRateScale()
    scale.add_bracket(0, 0)
    scale.add_bracket(2, 0)
    scale.add_bracket(4, 0)

    result = scale.bracket_indices(base, factor=2.0)

    tools.assert_near(result, [0, 0, 0, 0, 1, 1])


def test_bracket_indices_with_round_decimals() -> None:
    base = numpy.array([0, 1, 2, 3, 4, 5])
    scale = scales.AverageRateScale()
    scale.add_bracket(0, 0)
    scale.add_bracket(2, 0)
    scale.add_bracket(4, 0)

    result = scale.bracket_indices(base, round_decimals=0)

    tools.assert_near(result, [0, 0, 1, 1, 2, 2])


def test_bracket_indices_without_base() -> None:
    base = numpy.array([])
    scale = scales.AverageRateScale()
    scale.add_bracket(0, 0)
    scale.add_bracket(2, 0)
    scale.add_bracket(4, 0)

    with pytest.raises(scales.EmptyArgumentError):
        scale.bracket_indices(base)


def test_bracket_indices_without_brackets() -> None:
    base = numpy.array([0, 1, 2, 3, 4, 5])
    scale = scales.AverageRateScale()

    with pytest.raises(scales.EmptyArgumentError):
        scale.bracket_indices(base)


def test_to_dict() -> None:
    scale = scales.AverageRateScale()
    scale.add_bracket(0, 0)
    scale.add_bracket(100, 0.1)

    result = scale.to_dict()

    assert result == {"0": 0.0, "100": 0.1}


def test_to_marginal() -> None:
    base = numpy.array([1, 1.5, 2, 2.5])
    scale = scales.AverageRateScale()
    scale.add_bracket(0, 0)
    scale.add_bracket(1, 0.1)
    scale.add_bracket(2, 0.2)

    result = scale.to_marginal()

    assert result.thresholds == [0, 1, 2]
    tools.assert_near(result.rates, [0.1, 0.3, 0.2], absolute_error_margin=0)
    tools.assert_near(
        result.calc(base),
        [0.1, 0.25, 0.4, 0.5],
        absolute_error_margin=0,
    )
