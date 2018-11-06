# -*- coding: utf-8 -*-

import numpy

from openfisca_core.rates import average_rate


def test_average_rate():
    '''Compute the average tax rate when the gross income is never zero'''
    target = numpy.array([1, 2, 3])
    result = average_rate(target, varying = 2)
    expected = numpy.array([.5, 0, -.5])
    numpy.testing.assert_equal(result, expected)


def test_average_rate_when_varying_is_zero():
    '''Compute the average tax rate when the varying gross income cross zero (yields infinity)'''
    target = numpy.array([1, 2, 3])
    result = average_rate(target, varying = 0)
    assert numpy.isinf(result[0]).all()
