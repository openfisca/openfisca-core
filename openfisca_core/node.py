# -*- coding: utf-8 -*-


from __future__ import division

import numpy as np


class Node(object):
    """A container for a numpy array"""

    def __init__(self, value, entity, simulation):
        self.value = value
        self.entity = entity
        self.simulation = simulation

    def __add__(self, other):
        assert self.entity is other.entity
        assert self.simulation is other.simulation

        new_array = self.value + other.value
        return Node(new_array, self.entity, self.simulation)
