# -*- coding: utf-8 -*-


import numpy


def average_rate(target = None, varying = None, trim = None):
    '''
    Computes the average rate of a targeted net income, according to the varying gross income.

    :param target: Targeted net income, numerator
    :param varying: Varying gross income, denominator
    :param trim: Lower and upper bound of average rate to return
    '''
    average_rate = 1 - target / varying
    if trim is not None:
        average_rate = numpy.where(average_rate <= max(trim), average_rate, numpy.nan)
        average_rate = numpy.where(average_rate >= min(trim), average_rate, numpy.nan)

    return average_rate


def marginal_rate(target = None, varying = None, trim = None):
    # target: numerator, varying: denominator
    marginal_rate = 1 - (target[:-1] - target[1:]) / (varying[:-1] - varying[1:])
    if trim is not None:
        marginal_rate = numpy.where(marginal_rate <= max(trim), marginal_rate, numpy.nan)
        marginal_rate = numpy.where(marginal_rate >= min(trim), marginal_rate, numpy.nan)

    return marginal_rate
