# -*- coding: utf-8 -*-


"""Helpers to write formulas."""


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
