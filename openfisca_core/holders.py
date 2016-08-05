# -*- coding: utf-8 -*-


from __future__ import division

import numpy as np


class DatedHolder(object):
    """A view of an holder, for a given period (and possibly a given set of extra parameters).
    If the variable is not cached, it also contains the value of the variable for the given date."""
    formula = None
    period = None
    extra_params = None

    def __init__(self, formula, value, period, extra_params=None):
        self.formula = formula
        self.value = value
        self.period = period
        self.extra_params = extra_params

    def __add__(self, other):
        assert self.period == other.period

        new_array = self.value + other.value
        return DatedHolder(None, new_array, self.period)
