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
    """

    assert len(thresholds) == len(choice_list) - 1, "There must be one more outpu than threshold on apply_threshold"
    condlist = [input <= threshold for threshold in thresholds] + [True]

    return np.select(condlist, choice_list)
