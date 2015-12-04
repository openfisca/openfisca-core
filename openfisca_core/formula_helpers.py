# -*- coding: utf-8 -*-

"""Helpers to write formulas
"""

import numpy as np

def apply_threshold(input, thresholds, choice_list):
    """Returns one of the choices in choice_list depending on the inputs positions compared to thresholds
    
    >>>apply_threshold(numpy.array([4]), [5, 7], [10, 15, 20])
    [1O]
    >>>apply_threshold(numpy.array([5]), [5, 7], [10, 15, 20])
    [1O]
    >>>apply_threshold(numpy.array([6]), [5, 7], [10, 15, 20])
    [15]
    >>>apply_threshold(numpy.array([8]), [5, 7], [10, 15, 20])
    [20]
    >>>apply_threshold(numpy.array([10]), [5, 7, 9], [10, 15, 20])
    [0]
    """
    condlist = [input <= threshold for threshold in thresholds]
    if(len(condlist) == len(choice_list) - 1):
        condlist += [True] # If a choice is provided for input > highest threshold, last condition must be true to return it
    assert len(condlist) == len(choice_list), \
        "apply_threshold must be called with the same number of thresholds than choices, or one more choice"

    return np.select(condlist, choice_list)
