from typing import TypeVar

from openfisca_core.types import Array

T = TypeVar("T")


def empty_clone(original: T) -> T:
    """Creates an empty instance of the same class of the original object.

    Args:
        original: An object to clone.

    Returns:
        The cloned, empty, object.

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

    Dummy: object
    new: T

    Dummy = type(
        "Dummy",
        (original.__class__,),
        {"__init__": lambda self: None},
        )

    new = Dummy()
    new.__class__ = original.__class__
    return new


def stringify_array(array: Array) -> str:
    """Generates a clean string representation of a numpy array.

    Args:
        array: An array.

    Returns:
        :obj:`str`:
        "None" if the ``array`` is None, the stringified ``array`` otherwise.

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
