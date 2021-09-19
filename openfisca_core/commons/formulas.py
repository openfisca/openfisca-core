from typing import Any, Dict, List

import numpy

from openfisca_core.types import ArrayLike, ArrayType


def apply_thresholds(
        input: ArrayType[float],
        thresholds: ArrayLike[float],
        choices: ArrayLike[float],
        ) -> ArrayType[float]:
    """Makes a choice based on an input and thresholds.

    From list of ``choices``, it selects one of them based on a list of
    inputs, depending on the position of each ``input`` whithin a list of
    ``thresholds``. It does so for each ``input`` provided.

    Args:
        input: A list of inputs to make a choice.
        thresholds: A list of thresholds to choose.
        choices: A list of the possible choices.

    Returns:
        :obj:`numpy.ndarray` of :obj:`float`:
        A list of the choices made.

    Raises:
        :exc:`AssertionError`: When the number of ``thresholds`` (t) and the
            number of choices (c) are not either t == c or t == c - 1.

    Examples:
        >>> input = numpy.array([4, 5, 6, 7, 8])
        >>> thresholds = [5, 7]
        >>> choices = [10, 15, 20]
        >>> apply_thresholds(input, thresholds, choices)
        array([10, 10, 15, 15, 20])

    """

    condlist: List[ArrayType[bool]]

    condlist = [input <= threshold for threshold in thresholds]

    if len(condlist) == len(choices) - 1:
        # If a choice is provided for input > highest threshold, last condition
        # must be true to return it.
        condlist += [True]

    assert len(condlist) == len(choices), \
        " ".join([
            "apply_thresholds must be called with the same number of",
            "thresholds than choices, or one more choice",
            ])

    return numpy.select(condlist, choices)


def concat(this: ArrayLike[str], that: ArrayLike[str]) -> ArrayType[str]:
    """Concatenates the values of two arrays.

    Args:
        this: An array to concatenate.
        that: Another array to concatenate.

    Returns:
        :obj:`numpy.ndarray` of :obj:`float`:
        An array with the concatenated values.

    Examples:
        >>> this = ["this", "that"]
        >>> that = numpy.array([1, 2.5])
        >>> concat(this, that)
        array(['this1.0', 'that2.5']...)

    """

    if isinstance(this, numpy.ndarray) and \
       not numpy.issubdtype(this.dtype, numpy.str_):
        this = this.astype('str')

    if isinstance(that, numpy.ndarray) and \
       not numpy.issubdtype(that.dtype, numpy.str_):
        that = that.astype('str')

    return numpy.char.add(this, that)


def switch(
        conditions: ArrayType[float],
        value_by_condition: Dict[float, Any],
        ) -> ArrayType[float]:
    """Reproduces a switch statement.

    Given an array of conditions, returns an array of the same size,
    replacing each condition item by the corresponding given value.

    Args:
        conditions: An array of conditions.
        value_by_condition: Values to replace for each condition.

    Returns:
        :obj:`numpy.ndarray` of :obj:`float`:
        An array with the replaced values.

    Raises:
        :exc:`AssertionError`: When ``value_by_condition`` is empty.

    Examples:
        >>> conditions = numpy.array([1, 1, 1, 2])
        >>> value_by_condition = {1: 80, 2: 90}
        >>> switch(conditions, value_by_condition)
        array([80, 80, 80, 90])

    """

    assert len(value_by_condition) > 0, \
        "switch must be called with at least one value"

    condlist = [
        conditions == condition
        for condition in value_by_condition.keys()
        ]

    return numpy.select(condlist, value_by_condition.values())
