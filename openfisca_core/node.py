# -*- coding: utf-8 -*-


from __future__ import division

import numpy as np

from .numpy_wrapper import Shell


class Node(object):
    """A container for a numpy array"""

    def __init__(self, value, entity, simulation, default=None):
        self.value = value
        self.entity = entity
        self.simulation = simulation
        self.default = default

    def override(self, other, method):
        if isinstance(other, Node):
            assert self.entity is other.entity
            assert self.simulation is other.simulation
            other_value = other.value

        elif isinstance(other, Shell):
            other_value = other.value

        else:
            other_value = other

        new_array = getattr(self.value, method)(other_value)
        return Node(new_array, self.entity, self.simulation)

    def override_unary(self, method, *args, **kwargs):
        new_array = getattr(self.value, method)(*args, **kwargs)
        return Node(new_array, self.entity, self.simulation, self.default)

    def __and__(self, other):
        return self.override(other, '__and__')

    def __or__(self, other):
        return self.override(other, '__or__')

    def __truediv__(self, other):
        return self.override(other, '__truediv__')

    def __div__(self, other):
        return self.override(other, '__div__')

    def __add__(self, other):
        return self.override(other, '__add__')

    def __radd__(self, other):
        return self.override(other, '__radd__')

    def __sub__(self, other):
        return self.override(other, '__sub__')

    def __rsub__(self, other):
        return self.override(other, '__rsub__')

    def __mul__(self, other):
        return self.override(other, '__mul__')

    def __rmul__(self, other):
        return self.override(other, '__rmul__')

    def __eq__(self, other):
        return self.override(other, '__eq__')

    def __ne__(self, other):
        return self.override(other, '__ne__')

    def __lt__(self, other):
        return self.override(other, '__lt__')

    def __gt__(self, other):
        return self.override(other, '__gt__')

    def __le__(self, other):
        return self.override(other, '__le__')

    def __ge__(self, other):
        return self.override(other, '__ge__')

    def astype(self, *args, **kwargs):
        return self.override_unary('astype', *args, **kwargs)

    def __neg__(self):
        return self.override_unary('__neg__')

    def __getitem__(self, key):
        assert isinstance(key, Node)
        new_array = self.value[key.value]
        return Node(new_array, key.entity, self.simulation, self.default)

    def __setitem__(self, key, value):
        assert isinstance(key, Node)
        assert isinstance(value, Node)
        self.value[key.value] = value.value
        return None
