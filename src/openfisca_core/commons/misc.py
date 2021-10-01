import numpy


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
