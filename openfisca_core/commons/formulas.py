from __future__ import annotations

from collections.abc import Mapping

import numpy

from openfisca_core import types as t


def apply_thresholds(
    input: t.FloatArray,
    thresholds: t.ArrayLike[float],
    choices: t.ArrayLike[float],
) -> t.FloatArray:
    """Makes a choice based on an input and thresholds.

    From a list of ``choices``, this function selects one of these values
    based on a list of inputs, depending on the value of each ``input`` within
    a list of ``thresholds``.

    Args:
        input: A list of inputs to make a choice from.
        thresholds: A list of thresholds to choose.
        choices: A list of the possible values to choose from.

    Returns:
        ndarray[float32]: A list of the values chosen.

    Examples:
        >>> input = numpy.array([4, 5, 6, 7, 8])
        >>> thresholds = [5, 7]
        >>> choices = [10, 15, 20]
        >>> apply_thresholds(input, thresholds, choices)
        array([10, 10, 15, 15, 20])

    """
    condlist: list[t.Array[numpy.bool_] | bool]
    condlist = [input <= threshold for threshold in thresholds]

    if len(condlist) == len(choices) - 1:
        # If a choice is provided for input > highest threshold, last condition
        # must be true to return it.
        condlist += [True]

    msg = (
        "'apply_thresholds' must be called with the same number of thresholds "
        "than choices, or one more choice."
    )
    assert len(condlist) == len(choices), msg

    return numpy.select(condlist, choices)


def concat(
    this: t.StrArray | t.ArrayLike[object],
    that: t.StrArray | t.ArrayLike[object],
) -> t.StrArray:
    """Concatenate the values of two arrays.

    Args:
        this: An array to concatenate.
        that: Another array to concatenate.

    Returns:
        ndarray[str_]: An array with the concatenated values.

    Examples:
        >>> this = ["this", "that"]
        >>> that = numpy.array([1, 2.5])
        >>> concat(this, that)
        array(['this1.0', 'that2.5']...)

    """
    if not isinstance(this, numpy.ndarray):
        this = numpy.array(this)

    if not numpy.issubdtype(this.dtype, numpy.str_):
        this = this.astype("str")

    if not isinstance(that, numpy.ndarray):
        that = numpy.array(that)

    if not numpy.issubdtype(that.dtype, numpy.str_):
        that = that.astype("str")

    return numpy.char.add(this, that)


def switch(
    conditions: t.FloatArray | t.ArrayLike[float],
    value_by_condition: Mapping[float, float],
) -> t.FloatArray:
    """Mimic a switch statement.

    Given an array of conditions, returns an array of the same size,
    replacing each condition item with the matching given value.

    Args:
        conditions: An array of conditions.
        value_by_condition: Values to replace for each condition.

    Returns:
        ndarray[float32]: An array with the replaced values.

    Examples:
        >>> conditions = numpy.array([1, 1, 1, 2])
        >>> value_by_condition = {1: 80, 2: 90}
        >>> switch(conditions, value_by_condition)
        array([80, 80, 80, 90])

    """
    assert (
        len(value_by_condition) > 0
    ), "'switch' must be called with at least one value."

    condlist = [conditions == condition for condition in value_by_condition]

    return numpy.select(condlist, tuple(value_by_condition.values()))


__all__ = ["apply_thresholds", "concat", "switch"]
