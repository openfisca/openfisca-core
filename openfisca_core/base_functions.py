import numpy as np

from . import periods
from node import Node


def permanent_default_value(function, simulation, period, *extra_params):
    return function(simulation, period, *extra_params)


def requested_period_added_value(function, simulation, period, *extra_params):
    count = simulation.entity_data[variable.entity]['count']

    # This formula is used for variables that can be added to match requested period.
    period_size = period.size
    period_unit = period.unit
    if variable._array_by_period is not None and (period_size > 1 or period_unit == u'year'):
        after_instant = period.start.offset(period_size, period_unit)
        if period_size > 1:
            array = np.zeros(count, dtype=variable.dtype)
            sub_period = period.start.period(period_unit)
            while sub_period.start < after_instant:
                sub_array = variable._array_by_period.get(sub_period)
                if sub_array is None:
                    array = None
                    break
                array += sub_array
                sub_period = sub_period.offset(1)
            if array is not None:
                return period, Node(array, variable.entity, simulation)
        if period_unit == u'year':
            array = np.zeros(count, dtype=variable.dtype)
            month = period.start.period(u'month')
            while month.start < after_instant:
                month_array = variable._array_by_period.get(month)
                if month_array is None:
                    array = None
                    break
                array += month_array
                month = month.offset(1)
            if array is not None:
                return period, Node(array, variable.entity, simulation)
    if variable.function is not None:
        return variable.function(simulation, period, *extra_params)
    array = np.empty(count, dtype=variable.dtype)
    array.fill(variable.default)
    return period, Node(array, variable.entity, simulation)


def requested_period_default_value(variable, simulation, period, *extra_params):
    if variable.function is not None:
        return variable.function(simulation, period, *extra_params)

    count = simulation.entity_data[variable.entity]['count']
    array = np.empty(count, dtype=variable.dtype)
    array.fill(variable.default)
    return period, Node(array, variable.entity, simulation)


def requested_period_default_value_neutralized(variable, simulation, period, *extra_params):
    count = simulation.entity_data[variable.entity]['count']
    array = np.empty(count, dtype=variable.dtype)
    array.fill(variable.default)
    return period, Node(array, variable.entity, simulation)


def requested_period_last_value(variable, simulation, period, *extra_params, **kwargs):
    # This formula is used for variables that are constants between events and period size independent.
    # It returns the latest known value for the requested period.
    accept_future_value = kwargs.pop('accept_future_value', False)
    if variable._array_by_period:
        known_values = sorted(variable._array_by_period.iteritems(), reverse=True)
        for last_period, last_array in known_values:
            if last_period.start <= period.start and (variable.function is None or last_period.stop >= period.stop):
                return period, Node(last_array, variable.entity, simulation)
        if accept_future_value:
            next_period, next_array = known_values[-1]
            return period, Node(last_array, variable.entity, simulation)
    if variable.function is not None:
        return variable.function(simulation, period, *extra_params)

    count = simulation.entity_data[variable.entity]['count']
    array = np.empty(count, dtype=variable.dtype)
    array.fill(variable.default)
    return period, Node(array, variable.entity, simulation)


def requested_period_last_or_next_value(variable, simulation, period, *extra_params):
    # This formula is used for variables that are constants between events and period size independent.
    # It returns the latest known value for the requested period, or the next value if there is no past value.
    return requested_period_last_value(variable, simulation, period, *extra_params, accept_future_value=True)


def last_duration_last_value(variable, simulation, period, *extra_params):
    # This formula is used for variables that are constants between events but are period size dependent.
    # It returns the latest known value for the requested start of period but with the last period size.
    if variable._array_by_period is not None:
        for last_period, last_array in sorted(variable._array_by_period.iteritems(), reverse=True):
            if last_period.start <= period.start and (variable.function is None or last_period.stop >= period.stop):
                return periods.Period((last_period[0], period.start, last_period[2])), Node(last_array, variable.entity, simulation)
    if variable.function is not None:
        return variable.function(simulation, period, *extra_params)

    count = simulation.entity_data[variable.entity]['count']
    array = np.empty(count, dtype=variable.dtype)
    array.fill(variable.default)
    return period, Node(array, variable.entity, simulation)


def missing_value(variable, simulation, period):
    if variable.function is not None:
        return variable.function(simulation, period)

    raise ValueError(u"Missing value for variable {} at {}".format(variable.name, period))
