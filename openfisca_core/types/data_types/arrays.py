from typing import Sequence, TypeVar, Union

from nptyping import NDArray as ArrayType

T = TypeVar("T", bool, bytes, float, int, object, str)

A = Union[
    ArrayType[bool],
    ArrayType[bytes],
    ArrayType[float],
    ArrayType[int],
    ArrayType[object],
    ArrayType[str],
    ]

ArrayLike = Union[A, Sequence[T]]

""":obj:`.Generic`: Type of any castable to :class:`.ndarray`.

These include any :obj:`.ndarray` and sequences (like
:obj:`list`, :obj:`tuple`, and so on).

Examples:
    >>> ArrayLike[float]
    typing.Union[numpy.ndarray, typing.Sequence[float]]

    >>> ArrayLike[str]
    typing.Union[numpy.ndarray, typing.Sequence[str]]

Note:
    It is possible since numpy version 1.21 to specify the type of an
    array, thanks to `numpy.typing.NDArray`_:

    .. code-block:: python

        from numpy.typing import NDArray
        NDArray[numpy.float64]

    `mypy`_ provides `duck type compatibility`_, so an :obj:`int` is
    considered to be valid whenever a :obj:`float` is expected.

Todo:
    * Refactor once numpy version >= 1.21 is used.

.. versionadded:: 35.5.0

.. _mypy:
    https://mypy.readthedocs.io/en/stable/

.. _duck type compatibility:
    https://mypy.readthedocs.io/en/stable/duck_type_compatibility.html

.. _numpy.typing.NDArray:
    https://numpy.org/doc/stable/reference/typing.html#numpy.typing.NDArray

"""
