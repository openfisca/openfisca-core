from __future__ import annotations

import numexpr
import numpy

from openfisca_core import types as t


def empty_clone(original: object) -> object:
    """Create an empty instance of the same class of the original object.

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

    def __init__(_: object) -> None: ...

    Dummy = type(
        "Dummy",
        (original.__class__,),
        {"__init__": __init__},
    )

    new = Dummy()
    new.__class__ = original.__class__
    return new


def stringify_array(array: None | t.Array[numpy.generic]) -> str:
    """Generate a clean string representation of a numpy array.

    Args:
        array: An array.

    Returns:
        str: "None" if the ``array`` is None.
        str: The stringified ``array`` otherwise.

    Examples:
        >>> import numpy
        >>> stringify_array(None)
        'None'

        >>> array = numpy.array([10, 20.0])
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


def eval_expression(
    expression: str,
) -> str | t.Array[numpy.bool_] | t.Array[numpy.int32] | t.Array[numpy.float32]:
    """Evaluate a string expression to a numpy array.

    Args:
        expression: An expression to evaluate.

    Returns:
        Array: The result of the evaluation.
        str: The expression if it couldn't be evaluated.

    Examples:
        >>> eval_expression("1 + 2")
        array(3, dtype=int32)

        >>> eval_expression("salary")
        'salary'

    """

    try:
        return numexpr.evaluate(expression)

    except (KeyError, TypeError):
        return expression


__all__ = ["empty_clone", "eval_expression", "stringify_array"]
