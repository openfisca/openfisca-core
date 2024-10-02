import numpy
import pytest
from numpy.testing import assert_array_equal

from openfisca_core import commons


def test_apply_thresholds_when_several_inputs() -> None:
    """Make a choice for any given input."""

    input_ = numpy.array([4, 5, 6, 7, 8, 9, 10])
    thresholds = [5, 7, 9]
    choices = [10, 15, 20, 25]

    result = commons.apply_thresholds(input_, thresholds, choices)

    assert_array_equal(result, [10, 10, 15, 15, 20, 20, 25])


def test_apply_thresholds_when_too_many_thresholds() -> None:
    """Raise an AssertionError when thresholds > choices."""

    input_ = numpy.array([6])
    thresholds = [5, 7, 9, 11]
    choices = [10, 15, 20]

    with pytest.raises(AssertionError):
        assert commons.apply_thresholds(input_, thresholds, choices)


def test_apply_thresholds_when_too_many_choices() -> None:
    """Raise an AssertionError when thresholds < choices - 1."""

    input_ = numpy.array([6])
    thresholds = [5, 7]
    choices = [10, 15, 20, 25]

    with pytest.raises(AssertionError):
        assert commons.apply_thresholds(input_, thresholds, choices)


def test_concat_when_this_is_array_not_str() -> None:
    """Cast ``this`` to ``str`` when it is a NumPy array other than string."""

    this = numpy.array([1, 2])
    that = numpy.array(["la", "o"])

    result = commons.concat(this, that)

    assert_array_equal(result, ["1la", "2o"])


def test_concat_when_that_is_array_not_str() -> None:
    """Cast ``that`` to ``str`` when it is a NumPy array other than string."""

    this = numpy.array(["ho", "cha"])
    that = numpy.array([1, 2])

    result = commons.concat(this, that)

    assert_array_equal(result, ["ho1", "cha2"])


def test_concat_when_args_not_str_array_like() -> None:
    """Cast ``this`` and ``that`` to a NumPy array or strings."""

    this = (1, 2)
    that = (3, 4)

    result = commons.concat(this, that)

    assert_array_equal(result, ["13", "24"])


def test_switch_when_values_are_empty() -> None:
    """Raise an AssertionError when the values are empty."""

    conditions = [1, 1, 1, 2]
    value_by_condition = {}

    with pytest.raises(AssertionError):
        assert commons.switch(conditions, value_by_condition)
