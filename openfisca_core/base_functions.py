# -*- coding: utf-8 -*-


import numpy as np

from . import periods


def permanent_default_value(formula, simulation, period, *extra_params):
    if formula.function is not None:
        return formula.function(simulation, period, *extra_params)
    holder = formula.holder
    column = holder.column
    array = np.empty(holder.entity.count, dtype = column.dtype)
    array.fill(column.default)
    return period, array


def requested_period_added_value(formula, simulation, period, *extra_params):
    # This formula is used for variables that can be added to match requested period.
    holder = formula.holder
    column = holder.column
    period_size = period.size
    period_unit = period.unit
    if holder._array_by_period is not None and (period_size > 1 or period_unit == u'year'):
        after_instant = period.start.offset(period_size, period_unit)
        if period_size > 1:
            array = formula.zeros(dtype = column.dtype)
            sub_period = period.start.period(period_unit)
            while sub_period.start < after_instant:
                sub_array = holder._array_by_period.get(sub_period)
                if sub_array is None:
                    array = None
                    break
                array += sub_array
                sub_period = sub_period.offset(1)
            if array is not None:
                return period, array
        if period_unit == u'year':
            array = formula.zeros(dtype = column.dtype)
            month = period.start.period(u'month')
            while month.start < after_instant:
                month_array = holder._array_by_period.get(month)
                if month_array is None:
                    array = None
                    break
                array += month_array
                month = month.offset(1)
            if array is not None:
                return period, array
    if formula.function is not None:
        return formula.function(simulation, period, *extra_params)
    array = np.empty(holder.entity.count, dtype = column.dtype)
    array.fill(column.default)
    return period, array


def requested_period_default_value(formula, simulation, period, *extra_params):
    if formula.function is not None:
        return formula.function(simulation, period, *extra_params)
    holder = formula.holder
    column = holder.column
    array = np.empty(holder.entity.count, dtype = column.dtype)
    array.fill(column.default)
    return period, array


def requested_period_default_value_neutralized(formula, simulation, period, *extra_params):
    holder = formula.holder
    column = holder.column
    array = np.empty(holder.entity.count, dtype = column.dtype)
    array.fill(column.default)
    return period, array


def requested_period_last_value(formula, simulation, period, *extra_params, **kwargs):
    # This formula is used for variables that are constants between events and period size independent.
    # It returns the latest known value for the requested period.
    accept_future_value = kwargs.pop('accept_future_value', False)
    holder = formula.holder
    if holder._array_by_period is not None:
        known_values = sorted(holder._array_by_period.iteritems(), reverse = True)
        for last_period, last_result in known_values:
            if last_period.start <= period.start and (formula.function is None or last_period.stop >= period.stop):
                if type(last_result) == np.ndarray and not extra_params:
                    return period, last_result
                elif last_result.get(extra_params):
                        return period, last_result.get(extra_params)
        if accept_future_value:
            next_period, next_array = known_values[-1]
            return period, last_result
    if formula.function is not None:
        return formula.function(simulation, period, *extra_params)
    column = holder.column
    array = np.empty(holder.entity.count, dtype = column.dtype)
    array.fill(column.default)
    return period, array


def requested_period_last_or_next_value(formula, simulation, period, *extra_params):
    # This formula is used for variables that are constants between events and period size independent.
    # It returns the latest known value for the requested period, or the next value if there is no past value.
    return requested_period_last_value(formula, simulation, period, *extra_params, accept_future_value = True)


def last_duration_last_value(formula, simulation, period, *extra_params):
    # This formula is used for variables that are constants between events but are period size dependent.
    # It returns the latest known value for the requested start of period but with the last period size.
    holder = formula.holder
    if holder._array_by_period is not None:
        for last_period, last_result in sorted(holder._array_by_period.iteritems(), reverse = True):
            if last_period.start <= period.start and (formula.function is None or last_period.stop >= period.stop):
                output_period = periods.Period((last_period[0], period.start, last_period[2]))
                if type(last_result) == np.ndarray and not extra_params:
                    return output_period, last_result
                elif last_result.get(extra_params):
                    return output_period, last_result.get(extra_params)
    if formula.function is not None:
        return formula.function(simulation, period, *extra_params)
    column = holder.column
    array = np.empty(holder.entity.count, dtype = column.dtype)
    array.fill(column.default)
    return period, array
