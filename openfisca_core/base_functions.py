# -*- coding: utf-8 -*-

from . import periods


def requested_period_default_value(holder, period, *extra_params):
    array = holder.default_array()
    return array


def requested_period_last_value(holder, period, *extra_params, **kwargs):
    """
        This formula is used for variables that are constants between events and period size independent.
        If the variable has no formula, it will return the latest known value of the variable
    """

    accept_future_value = kwargs.pop('accept_future_value', False)
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


def requested_period_last_or_next_value(holder, period, *extra_params):
    """
        This formula is used for variables that are constants between events and period size independent.
        If the variable has no formula, it will return the latest known value of the variable, or the next value if there is no past value.
    """
    return requested_period_last_value(holder, period, *extra_params, accept_future_value = True)


def missing_value(holder, period, *extra_params):
    variable = holder.variable
    raise ValueError(u"Missing value for variable {} at {}".format(variable.name, period))
