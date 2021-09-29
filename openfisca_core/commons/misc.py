from typing import Any

from openfisca_core.types import ArrayType


def empty_clone(original: Any) -> Any:
    """Creates an empty instance of the same class of the original object.

    Note:
        We ignore the type of ``original`` because there's a bug in MyPy:
        https://github.com/python/mypy/issues/4177

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

    class Dummy(original.__class__):  # type: ignore
        def __init__(self) -> None:
            pass

    new = Dummy()
    new.__class__ = original.__class__
    return new


def stringify_array(array: ArrayType) -> str:
    """Generates a clean string representation of a numpy array.

    Args:
        array: An array.

    Returns:
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
