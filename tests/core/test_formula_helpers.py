import numpy
import pytest

from openfisca_core.formula_helpers import apply_thresholds
from openfisca_core.tools import assert_near


def test_apply_thresholds_with_too_many_thresholds():
    input = numpy.array([10])
    thresholds = [5, 4]
    choice_list = [10]
    with pytest.raises(AssertionError):
        return apply_thresholds(input, thresholds, choice_list)


def test_apply_thresholds_with_too_few_thresholds():
    input = numpy.array([10])
    thresholds = [5]
    choice_list = [10, 15, 20]
    with pytest.raises(AssertionError):
        return apply_thresholds(input, thresholds, choice_list)


def test_apply_thresholds():
    input = numpy.array([4, 5, 6, 7, 8])
    thresholds = [5, 7]
    choice_list = [10, 15, 20]
    result = apply_thresholds(input, thresholds, choice_list)
    assert_near(result, [10, 10, 15, 15, 20])


def test_apply_thresholds_with_as_many_thresholds_than_choices():
    input = numpy.array([4, 6, 8])
    thresholds = [5, 7]
    choice_list = [10, 20]
    result = apply_thresholds(input, thresholds, choice_list)
    assert_near(result, [10, 20, 0])


def test_apply_thresholds_with_variable_threshold():
    input = numpy.array([1000, 1000, 1000])
    thresholds = [numpy.array([500, 1500, 1000])]  # Only one thresold, but varies with the person
    choice_list = [True, False]  # True if input <= threshold, false otherwise
    result = apply_thresholds(input, thresholds, choice_list)
    assert_near(result, [False, True, True])
