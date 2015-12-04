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
    if(len(thresholds) == len(choice_list)):
    	choice_list += [0] # If no choice is provided for input > highest threshold, return 0
    assert len(thresholds) == len(choice_list) - 1, \
    	"apply_threshold must be called with the same number of thresholds than choices, or one more choice"
    condlist = [input <= threshold for threshold in thresholds] + [True]

    return np.select(condlist, choice_list)
