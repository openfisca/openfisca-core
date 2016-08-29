# -*- coding: utf-8 -*-

import numpy
from nose.tools import raises

from openfisca_core.node import Node
from openfisca_core.formula_helpers import apply_thresholds as apply_thresholds
from openfisca_core.tools import assert_near


@raises(AssertionError)
def test_apply_thresholds_with_too_many_thresholds():
    input = Node(numpy.array([10]), None, None, None)
    thresholds = [5, 4]
    choice_list = [10]
    return apply_thresholds(input, thresholds, choice_list).value


@raises(AssertionError)
def test_apply_thresholds_with_too_few_thresholds():
    input = Node(numpy.array([10]), None, None, None)
    thresholds = [5]
    choice_list = [10, 15, 20]
    return apply_thresholds(input, thresholds, choice_list).value


def test_apply_thresholds():
    input = Node(numpy.array([4, 5, 6, 7, 8]), None, None, None)
    thresholds = [5, 7]
    choice_list = [10, 15, 20]
    result = apply_thresholds(input, thresholds, choice_list)
    assert_near(result.value, [10, 10, 15, 15, 20])


def test_apply_thresholds_with_as_many_thresholds_than_choices():
    input = Node(numpy.array([4, 6, 8]), None, None, None)
    thresholds = [5, 7]
    choice_list = [10, 20]
    result = apply_thresholds(input, thresholds, choice_list)
    assert_near(result.value, [10, 20, 0])


def test_apply_thresholds_with_variable_threshold():
    input = Node(numpy.array([1000, 1000, 1000]), None, None, None)
    thresholds = [Node(numpy.array([500, 1500, 1000]), None, None, None)]  # Only one thresold, but varies with the person
    choice_list = [True, False]  # True if input <= threshold, false otherwise
    result = apply_thresholds(input, thresholds, choice_list)
    assert_near(result.value, [False, True, True])
