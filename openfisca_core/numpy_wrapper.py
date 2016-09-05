from functools import partial

import numpy as np

from node import Node, Shell

int16 = np.int16


def mixed_type_function(function, l):
    entity = None
    simulation = None
    values = []

    for x in l:
        if isinstance(x, Node):
            values.append(x.value)
            entity = x.entity
            simulation = x.simulation
        elif isinstance(x, Shell):
            values.append(x.value)
        else:
            values.append(x)

    array = function(*values)

    if entity:
        return Node(array, entity, simulation)
    else:
        return Shell(array)


def maximum(x1, x2):
    return mixed_type_function(np.maximum, [x1, x2])

def minimum(x1, x2):
    return mixed_type_function(np.minimum, [x1, x2])

def datetime64(*args, **kwargs):
    value = np.datetime64(*args, **kwargs)
    return Shell(value)

def timedelta64(*args, **kwargs):
    value = np.timedelta64(*args, **kwargs)
    return Shell(value)

def logical_or(x1, x2):
    array = np.logical_or(x1.value, x2.value)
    return Node(array, x1.entity, x1.simulation)

def logical_and(x1, x2):
    array = np.logical_and(x1.value, x2.value)
    return Node(array, x1.entity, x1.simulation)

def logical_xor(x1, x2):
    array = np.logical_xor(x1.value, x2.value)
    return Node(array, x1.entity, x1.simulation)

def logical_not(x):
    if isinstance(x, Node):
        array = np.logical_not(x.value)
        return Node(array, x.entity, x.simulation)
    else:
        return np.logical_not(x)

def round(a, decimals=0):
    if isinstance(a, Node):
        array = np.round(a.value, decimals=decimals)
        return Node(array, a.entity, a.simulation)
    else:
        return np.round(a, decimals=decimals)

def around(a, decimals=0):
    return round(a, decimals=decimals)

def select(condlist, choicelist, default=0):
    for cond in condlist:
        assert isinstance(cond, Node)

    array = np.select([cond.value for cond in condlist],
        [choice.value if isinstance(choice, Node) else choice for choice in choicelist],
        default.value if isinstance(default, Node) else default)

    return Node(array, condlist[0].entity, condlist[0].simulation)

def busday_count(begindates, enddates, weekmask, holidays=[]):
    partial_busday_count = partial(np.busday_count, weekmask=weekmask, holidays=holidays)

    return mixed_type_function(partial_busday_count, [begindates, enddates])

def startswith(a, prefix):
    array = np.core.defchararray.startswith(a.value, prefix)
    return Node(array, a.entity, a.simulation)

def floor(x):
    array = np.floor(x.value)
    return Node(array, x.entity, x.simulation)

def ceil(x):
    array = np.ceil(x.value)
    return Node(array, x.entity, x.simulation)

def where(condition, x, y):
    return mixed_type_function(np.where, [condition, x, y])

def fromiter():
    raise Exception()

def take(a, indices):
    array = np.take(a, indices.value)
    return Node(array, indices.entity, indices.simulation)

def absolute(x):
    array = np.absolute(x.value)
    return Node(array, x.entity, x.simulation)

def abs(x):
    array = np.abs(x.value)
    return Node(array, x.entity, x.simulation)

def errstate(**kwargs):
    return np.errstate(**kwargs)

def vector_map(x, f):
    assert isinstance(x, Node)

    n = len(x.value)
    input_array = x.value.reshape((n, 1))

    array = np.apply_along_axis(lambda v: f(v[0]), 1, input_array)

    array_output = array.reshape(n)

    return Node(array_output, x.entity, x.simulation)
