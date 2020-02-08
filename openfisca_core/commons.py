import warnings

import numpy


class Dummy(object):
    """A class that does nothing."""

    def __init__(self) -> None:
        message = [
            "The 'Dummy' class has been deprecated since version 34.7.0,",
            "and will be removed in the future.",
            ]
        warnings.warn(" ".join(message), DeprecationWarning)
        pass


def empty_clone(original):
    """Create a new empty instance of the same class of the original object."""
    class Dummy(original.__class__):
        def __init__(self) -> None:
            pass

    new = Dummy()
    new.__class__ = original.__class__
    return new


def stringify_array(array: numpy.ndarray) -> str:
    """
    Generate a clean string representation of a NumPY array.
    """

    if array is None:
        return "None"

    return f"[{', '.join(str(cell) for cell in array)}]"
