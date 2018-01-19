# -*- coding: utf-8 -*-

import warnings

from . import periods


def permanent_default_value(formula, simulation, period, *extra_params):
    warnings.warn(
        u"permanent_default_value is deprecated"
        u"permanent_default_value has the same effect "
        u"than requested_period_default_value, the default base_function for float and int variables. "
        u"There is thus no need to specifiy it. ",
        Warning
        )

    return requested_period_default_value(formula, simulation, period, *extra_params)


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
    """
        This formula is used for variables that are constants between events and period size independent.
        If the variable has no formula, it will return the latest known value of the variable
    """

    function = formula.find_function(period)
    if function is not None:
        return formula.exec_function(simulation, period, *extra_params)

    accept_future_value = kwargs.pop('accept_future_value', False)
    holder = formula.holder
    known_periods = holder.get_known_periods()
    if not known_periods:
        return holder.default_array()
    known_periods = sorted(known_periods, cmp = periods.compare_period_start, reverse = True)
    for last_period in known_periods:
        if last_period.start <= period.start:
            return holder.get_array(last_period, extra_params)
    if accept_future_value:
        next_period = known_periods[-1]
        return holder.get_array(next_period, extra_params)
    return holder.default_array()


def requested_period_last_or_next_value(formula, simulation, period, *extra_params):
    """
        This formula is used for variables that are constants between events and period size independent.
        If the variable has no formula, it will return the latest known value of the variable, or the next value if there is no past value.
    """
    return requested_period_last_value(formula, simulation, period, *extra_params, accept_future_value = True)


def missing_value(formula, simulation, period, *extra_params):
    function = formula.find_function(period)
    if function is not None:
        return formula.exec_function(simulation, period, *extra_params)
    holder = formula.holder
    variable = holder.variable
    raise ValueError(u"Missing value for variable {} at {}".format(variable.name, period))
