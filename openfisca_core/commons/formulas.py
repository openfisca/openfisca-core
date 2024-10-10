from __future__ import annotations

from collections.abc import Mapping

import numpy
from numba import (  # pyright: ignore[reportMissingImports,reportMissingTypeStubs]
    float32,
    guvectorize,
)

from . import types as t


@guvectorize(
    [(float32[:], float32[:], float32[:], float32[:])], "(n),(o),(p)->(n)"
)  # pyright: ignore[reportUnknownMemberType,reportUntypedFunctionDecorator]
def apply_thresholds(
    input: t.FloatArray,
    thresholds: t.FloatArray,
    choices: t.FloatArray,
    result: t.FloatArray,
) -> None:
    """Make a choice based on an input and thresholds.

    From a list of ``choices``, this function selects one of these values
    based on a list of inputs, depending on the value of each ``input`` within
    a list of ``thresholds``.

    Args:
        input: A list of inputs to make a choice from.
        thresholds: A list of thresholds to choose.
        choices: A list of the possible values to choose from.
        result: A list of the values chosen.

    Raises:
        ValueError: When the number of ``thresholds`` is not equal to the
            number of ``choices``, or one less.

    Examples:
        >>> input = numpy.array([4, 5, 6, 7, 8], dtype=numpy.float32)
        >>> thresholds = numpy.array([5, 7], dtype=numpy.float32)
        >>> choices = numpy.array([10, 15, 20], dtype=numpy.float32)
        >>> apply_thresholds(input, thresholds, choices)
        array([10., 10., 15., 15., 20.], dtype=float32)

    """
    condlist = [numpy.array([x], dtype=t.BoolDType) for x in range(0)]

    for threshold in thresholds:
        condlist.append(input <= threshold)  # noqa: PERF401

    choicelist = [numpy.array([x], dtype=t.FloatDType) for x in range(0)]

    for choice in choices:
        choicelist.append(numpy.array([choice], dtype=t.FloatDType))  # noqa: PERF401

    if len(condlist) == len(choicelist) - 1:
        # If a choice is provided for input > highest threshold, last condition
        # must be true to return it.
        condlist.append(numpy.array([True], dtype=t.BoolDType))

    if len(condlist) != len(choicelist):
        msg = (
            "'apply_thresholds' must be called with the same number of "
            "thresholds than choices, or one more choice."
        )
        raise ValueError(msg)

    array = numpy.select(condlist, choicelist)

    for i in range(array.size):
        result[i] = array[i]


def concat(
    this: t.Array[numpy.str_] | t.ArrayLike[object],
    that: t.Array[numpy.str_] | t.ArrayLike[object],
) -> t.Array[numpy.str_]:
    """Concatenate the values of two arrays.

    Args:
        this: An array to concatenate.
        that: Another array to concatenate.

    Returns:
        Array[numpy.str_]: An array with the concatenated values.

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
    conditions: t.Array[numpy.float32] | t.ArrayLike[float],
    value_by_condition: Mapping[float, float],
) -> t.Array[numpy.float32]:
    """Mimick a switch statement.

    Given an array of conditions, returns an array of the same size,
    replacing each condition item with the matching given value.

    Args:
        conditions: An array of conditions.
        value_by_condition: Values to replace for each condition.

    Returns:
        Array: An array with the replaced values.

    Raises:
        AssertionError: When ``value_by_condition`` is empty.

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
