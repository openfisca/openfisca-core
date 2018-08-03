# -*- coding: utf-8 -*-


"""Helpers to write formulas."""
from __future__ import unicode_literals, print_function, division, absolute_import


import numpy as np


def apply_thresholds(input, thresholds, choices):
    """
    Return one of the choices depending on the input position compared to thresholds, for each input.

    >>> apply_thresholds(np.array([4]), [5, 7], [10, 15, 20])
    array([10])
    >>> apply_thresholds(np.array([5]), [5, 7], [10, 15, 20])
    array([10])
    >>> apply_thresholds(np.array([6]), [5, 7], [10, 15, 20])
    array([15])
    >>> apply_thresholds(np.array([8]), [5, 7], [10, 15, 20])
    array([20])
    >>> apply_thresholds(np.array([10]), [5, 7, 9], [10, 15, 20])
    array([0])
    """
    condlist = [input <= threshold for threshold in thresholds]
    if len(condlist) == len(choices) - 1:
        # If a choice is provided for input > highest threshold, last condition must be true to return it.
        condlist += [True]
    assert len(condlist) == len(choices), \
        "apply_thresholds must be called with the same number of thresholds than choices, or one more choice"
    return np.select(condlist, choices)


def switch(conditions, value_by_condition):
    '''
    Reproduces a switch statement: given an array of conditions, return an array of the same size replacing each
    condition item by the corresponding given value.

    Example:
        >>> switch(np.array([1, 1, 1, 2]), {1: 80, 2: 90})
        array([80, 80, 80, 90])
    '''
    condlist = [
        conditions == condition
        for condition in value_by_condition.keys()
        ]
    return np.select(condlist, value_by_condition.values())


def concat(this, that):
    if isinstance(this, np.ndarray) and not np.issubdtype(this.dtype, np.str):
        this = this.astype('str')
    if isinstance(that, np.ndarray) and not np.issubdtype(that.dtype, np.str):
        that = that.astype('str')

    return np.core.defchararray.add(this, that)
