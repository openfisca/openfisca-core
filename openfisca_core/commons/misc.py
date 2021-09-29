import numpy


def empty_clone(original):
    """Create a new empty instance of the same class of the original object.

    Examples:
        >>> Foo = type("Foo", (list,), {})
        >>> foo = Foo([1, 2, 3])
        >>> foo
        [1, 2, 3]

        >>> bar = empty_clone(foo)
        >>> bar
        []

        >>> isinstance(bar, Foo)
        True

    """

    class Dummy(original.__class__):
        def __init__(self) -> None:
            pass

    new = Dummy()
    new.__class__ = original.__class__
    return new


def stringify_array(array: numpy.ndarray) -> str:
    """
    Generate a clean string representation of a NumPY array.

    Examples:
        >>> import numpy
        >>> stringify_array(None)
        'None'

        >>> array = numpy.array([10, 20.])
        >>> stringify_array(array)
        '[10.0, 20.0]'

        >>> array = numpy.array(["10", "Twenty"])
        >>> stringify_array(array)
        '[10, Twenty]'

        >>> array = numpy.array([list, dict(), stringify_array])
        >>> stringify_array(array)
        "[<class 'list'>, {}, <function stringify_array...]"

    """

    if array is None:
        return "None"

    return f"[{', '.join(str(cell) for cell in array)}]"
