import logging

import numpy

from openfisca_core import periods

log = logging.getLogger(__name__)


def set_input_dispatch_by_period(holder, period, array) -> None:
    """This function can be declared as a ``set_input`` attribute of a variable.

    In this case, the variable will accept inputs on larger periods that its definition period, and the value for the larger period will be applied to all its subperiods.

    To read more about ``set_input`` attributes, check the `documentation <https://openfisca.org/doc/coding-the-legislation/35_periods.html#set-input-automatically-process-variable-inputs-defined-for-periods-not-matching-the-definition-period>`_.
    """
    array = holder._to_array(array)

    period_size = period.size
    period_unit = period.unit

    if holder.variable.definition_period not in (
        periods.DateUnit.isoformat + periods.DateUnit.isocalendar
    ):
        msg = "set_input_dispatch_by_period can't be used for eternal variables."
        raise ValueError(
            msg,
        )

    cached_period_unit = holder.variable.definition_period
    after_instant = period.start.offset(period_size, period_unit)

    # Cache the input data, skipping the existing cached months
    sub_period = periods.Period((cached_period_unit, period.start, 1))
    while sub_period.start < after_instant:
        existing_array = holder.get_array(sub_period)
        if existing_array is None:
            holder._set(sub_period, array)
        else:
            # The array of the current sub-period is reused for the next ones.
            # TODO: refactor or document this behavior
            array = existing_array
        sub_period = sub_period.offset(1)


def set_input_divide_by_period(holder, period, array) -> None:
    """This function can be declared as a ``set_input`` attribute of a variable.

    In this case, the variable will accept inputs on larger periods that its definition period, and the value for the larger period will be divided between its subperiods.

    To read more about ``set_input`` attributes, check the `documentation <https://openfisca.org/doc/coding-the-legislation/35_periods.html#set-input-automatically-process-variable-inputs-defined-for-periods-not-matching-the-definition-period>`_.
    """
    if not isinstance(array, numpy.ndarray):
        array = numpy.array(array)
    period_size = period.size
    period_unit = period.unit

    if holder.variable.definition_period not in (
        periods.DateUnit.isoformat + periods.DateUnit.isocalendar
    ):
        msg = "set_input_divide_by_period can't be used for eternal variables."
        raise ValueError(
            msg,
        )

    cached_period_unit = holder.variable.definition_period
    after_instant = period.start.offset(period_size, period_unit)

    # Count the number of elementary periods to change, and the difference with what is already known.
    remaining_array = array.copy()
    sub_period = periods.Period((cached_period_unit, period.start, 1))
    sub_periods_count = 0
    while sub_period.start < after_instant:
        existing_array = holder.get_array(sub_period)
        if existing_array is not None:
            remaining_array -= existing_array
        else:
            sub_periods_count += 1
        sub_period = sub_period.offset(1)

    # Cache the input data
    if sub_periods_count > 0:
        divided_array = remaining_array / sub_periods_count
        sub_period = periods.Period((cached_period_unit, period.start, 1))
        while sub_period.start < after_instant:
            if holder.get_array(sub_period) is None:
                holder._set(sub_period, divided_array)
            sub_period = sub_period.offset(1)
    elif not (remaining_array == 0).all():
        msg = f"Inconsistent input: variable {holder.variable.name} has already been set for all months contained in period {period}, and value {array} provided for {period} doesn't match the total ({array - remaining_array}). This error may also be thrown if you try to call set_input twice for the same variable and period."
        raise ValueError(
            msg,
        )
