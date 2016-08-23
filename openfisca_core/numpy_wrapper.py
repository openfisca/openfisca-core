import numpy as np

import node

class Shell:
    def __init__(self, value):
        self.value = value

    def __add__(self, other):
        if isinstance(other, Shell):
            return Shell(self.value + other.value)

        raise NotImplementedError()

def maximum(*args, **kwargs):
    return np.maximum(*args, **kwargs)

def minimum(*args, **kwargs):
    return np.minimum(*args, **kwargs)

def datetime64(*args, **kwargs):
    value = np.datetime64(*args, **kwargs)
    return Shell(value)

def timedelta64(*args, **kwargs):
    value = np.timedelta64(*args, **kwargs)
    return Shell(value)

def logical_and(*args, **kwargs):
    return np.logical_and(*args, **kwargs)

def logical_not(*args, **kwargs):
    return np.logical_not(*args, **kwargs)

def logical_or(*args, **kwargs):
    return np.logical_or(*args, **kwargs)

def logical_xor(*args, **kwargs):
    return np.logical_xor(*args, **kwargs)

def round(a, decimals=0):
    array = np.round(a.value, decimals)
    return node.Node(array, a.entity, a.simulation)

def select(condlist, choicelist, default=0):
    for cond in condlist:
        assert isinstance(cond, node.Node)

    array = np.select([cond.value for cond in condlist], choicelist, default)

    return node.Node(array, condlist[0].entity, condlist[0].simulation)


def busday_count(begindates, enddates, weekmask):
    assert isinstance(begindates, node.Node)
    assert isinstance(enddates, node.Node)

    array = np.busday_count(begindates.value, enddates.value, weekmask)
    return node.Node(array, begindates.entity, begindates.simulation)

def startswith(a, prefix):
    array = np.core.defchararray.startswith(a.value, prefix)
    return node.Node(array, a.entity, a.simulation)
