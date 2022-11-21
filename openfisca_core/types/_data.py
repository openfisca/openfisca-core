from typing import Sequence, TypeVar, Union

from nptyping import types, NDArray as Array

import numpy

T = TypeVar("T", bool, bytes, float, int, object, str)

types._ndarray_meta._Type = Union[type, numpy.dtype, TypeVar]

ArrayLike = Union[Array[T], Sequence[T]]
""":obj:`typing.Generic`: Type of any castable to :class:`numpy.ndarray`.

These include any :obj:`numpy.ndarray` and sequences (like
:obj:`list`, :obj:`tuple`, and so on).

Examples:
    >>> ArrayLike[float]
    typing.Union[numpy.ndarray, typing.Sequence[float]]

    >>> ArrayLike[str]
    typing.Union[numpy.ndarray, typing.Sequence[str]]

Note:
    It is possible since numpy version 1.21 to specify the type of an
    array, thanks to `numpy.typing.NDArray`_::

        from numpy.typing import NDArray
        NDArray[numpy.float64]

    `mypy`_ provides `duck type compatibility`_, so an :obj:`int` is
    considered to be valid whenever a :obj:`float` is expected.

Todo:
    * Refactor once numpy version >= 1.21 is used.

.. versionadded:: 35.5.0

.. versionchanged:: 35.6.0
    Moved to :mod:`.types`

.. _mypy:
    https://mypy.readthedocs.io/en/stable/

.. _duck type compatibility:
    https://mypy.readthedocs.io/en/stable/duck_type_compatibility.html

.. _numpy.typing.NDArray:
    https://numpy.org/doc/stable/reference/typing.html#numpy.typing.NDArray

"""
