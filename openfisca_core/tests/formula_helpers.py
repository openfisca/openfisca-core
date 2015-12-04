# -*- coding: utf-8 -*-

import numpy
from nose.tools import raises

from openfisca_core.formula_helpers import apply_threshold as apply_threshold
from openfisca_core.tools import assert_near

@raises(AssertionError)
def test_apply_threshold_with_too_many_thresholds():
    input = numpy.array([10])
    thresholds = [5]
    outputs = [10]
    return apply_threshold(input, thresholds, outputs)

@raises(AssertionError)
def test_apply_threshold_with_too_few_thresholds():
    input = numpy.array([10])
    thresholds = [5]
    outputs = [10, 15, 20]
    return apply_threshold(input, thresholds, outputs)

def test_apply_threshold():
    input = numpy.array([4, 5, 6, 7, 8])
    thresholds = [5, 7]
    outputs = [10, 15, 20]
    result = apply_threshold(input, thresholds, outputs)
    assert_near(result, [10, 10, 15, 15, 20])
