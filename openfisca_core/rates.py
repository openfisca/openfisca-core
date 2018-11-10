# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import

import numpy


def average_rate(target = None, varying = None):
    '''
    Computes the average rate of a targeted net income, according to the varying gross income.

    :param target: Targeted net income, numerator
    :param varying: Varying gross income, denominator
    '''
    return 1 - target / varying


def marginal_rate(target = None, varying = None, trim = None):
    # target: numerator, varying: denominator
    marginal_rate = 1 - (target[:-1] - target[1:]) / (varying[:-1] - varying[1:])
    if trim is not None:
        marginal_rate = numpy.where(marginal_rate <= max(trim), marginal_rate, numpy.nan)
        marginal_rate = numpy.where(marginal_rate >= min(trim), marginal_rate, numpy.nan)

    return marginal_rate
