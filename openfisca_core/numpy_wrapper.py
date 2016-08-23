import numpy as np

class Shell:
    def __init__(self, value):
        self.value = value

def maximum(*args, **kwargs):
    return np.maximum(*args, **kwargs)

def minimum(*args, **kwargs):
    return np.minimum(*args, **kwargs)

def datetime64(*args, **kwargs):
    array = np.datetime64(*args, **kwargs)
    return Shell(array)

def logical_and(*args, **kwargs):
    return np.logical_and(*args, **kwargs)

def logical_not(*args, **kwargs):
    return np.logical_not(*args, **kwargs)

def logical_or(*args, **kwargs):
    return np.logical_or(*args, **kwargs)

def logical_xor(*args, **kwargs):
    return np.logical_xor(*args, **kwargs)

def round(*args, **kwargs):
    return np.round(*args, **kwargs)
