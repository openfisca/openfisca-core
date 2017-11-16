# -*- coding: utf-8 -*-

import warnings

import numpy as np

from . import periods

# TODO: Adapt base_functions to cache disk

def permanent_default_value(formula, simulation, period, *extra_params):
    if formula.find_function(period) is not None:
        return formula.exec_function(simulation, period, *extra_params)
    holder = formula.holder
    array = holder.default_array()
    return array


def requested_period_added_value(formula, simulation, period, *extra_params):
    warnings.warn(
        u"requested_period_added_value is deprecated. "
        u"Since OpenFisca Core 6.0, requested_period_added_value has the same effect "
        u"than requested_period_default_value, the default base_function for float and int variables. "
        u"There is thus no need to specifiy it. ",
        Warning
        )
    return requested_period_default_value(formula, simulation, period, *extra_params)


def requested_period_default_value(formula, simulation, period, *extra_params):
    if formula.find_function(period) is not None:
        return formula.exec_function(simulation, period, *extra_params)
    holder = formula.holder
    array = holder.default_array()
    return array


def requested_period_last_value(formula, simulation, period, *extra_params, **kwargs):
    # This formula is used for variables that are constants between events and period size independent.
    # It returns the latest known value for the requested period.

    def compare_start_instant(x, y):
        a = x[0]  # x = (period, array)
        b = y[0]

        return periods.compare_period_start(a, b)

    accept_future_value = kwargs.pop('accept_future_value', False)
    holder = formula.holder
    function = formula.find_function(period)
    # TODO We should take the cache disk into account
    if holder._array_by_period:
        known_values = sorted(holder._array_by_period.iteritems(), cmp = compare_start_instant, reverse = True)
        for last_period, last_result in known_values:
            if last_period.start <= period.start and (function is None or last_period.stop >= period.stop):
                if isinstance(last_result, np.ndarray) and not extra_params:
                    return last_result
                elif last_result.get(extra_params):
                        return last_result.get(extra_params)
        if accept_future_value:
            next_period, next_array = known_values[-1]
            return last_result
    if function is not None:
        return formula.exec_function(simulation, period, *extra_params)
    array = holder.default_array()
    return array


def requested_period_last_or_next_value(formula, simulation, period, *extra_params):
    # This formula is used for variables that are constants between events and period size independent.
    # It returns the latest known value for the requested period, or the next value if there is no past value.
    return requested_period_last_value(formula, simulation, period, *extra_params, accept_future_value = True)


def missing_value(formula, simulation, period, *extra_params):
    function = formula.find_function(period)
    if function is not None:
        return formula.exec_function(simulation, period, *extra_params)
    holder = formula.holder
    variable = holder.variable
    raise ValueError(u"Missing value for variable {} at {}".format(variable.name, period))
