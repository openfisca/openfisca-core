# -*- coding: utf-8 -*-


"""
    base_function is an optional variable attribute that can optionally be set to one of the functions defined in this module.

    If a variable is calculated at a period for which it does not have a formulas, its base_function will be called to try to infere a value based on past or future values of the variable.
"""

from __future__ import unicode_literals, print_function, division, absolute_import


def requested_period_default_value(holder, period, *extra_params):
    """
        This formula is used for variables for which we don't want to make any inference about the value for a given period based on past or future values.

        Having this `base_function` is strictly equivalent to not having a `base_function`, but it can still be needed to overwrite an unwanted default `base_function`.
    """
    return None


def requested_period_last_value(holder, period, *extra_params, **kwargs):
    """
        This formula is used for variables that are constants between events and period size independent.
        If the variable has no formula, it will return the latest known value of the variable
    """

    accept_future_value = kwargs.pop('accept_future_value', False)
    known_periods = holder.get_known_periods()
    if not known_periods:
        return holder.default_array()
    known_periods = sorted(known_periods, key=lambda period: period.start, reverse = True)
    for last_period in known_periods:
        if last_period.start <= period.start:
            return holder.get_array(last_period, extra_params)
    if accept_future_value:
        next_period = known_periods[-1]
        return holder.get_array(next_period, extra_params)
    return None


def requested_period_last_or_next_value(holder, period, *extra_params):
    """
        This formula is used for variables that are constants between events and period size independent.
        If the variable has no formula, it will return the latest known value of the variable, or the next value if there is no past value.
    """
    return requested_period_last_value(holder, period, *extra_params, accept_future_value = True)


def missing_value(holder, period, *extra_params):
    raise ValueError("Missing value for variable {} at {}".format(holder.variable.name, period))
