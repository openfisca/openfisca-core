from __future__ import annotations

import dataclasses
import typing

from .axis import Axis


@dataclasses.dataclass(frozen = True)
class AxisArray:
    """
    Simply a collection of :class:`Axis`.

    Axis expansion is a feature in :module:`openfisca_core` that allows us to
    parametrise some dimensions in order to create and to evaluate a range of
    values for others.

    The most typical use of axis expansion is evaluate different numerical
    values, starting from a :attr:`min_` and up to a :attr:`max_`, that could
    take any given :class:`openfisca_core.variables.Variable` for any given
    :class:`openfisca_core.periods.Period` for any given population (or a
    collection of :module:`openfisca_core.entities`).

    Attributes:

        axes:   A :type:`tuple` containing our collection of :class:`Axis`.

    Usage:

        >>> axis_array = AxisArray()
        >>> axis_array
        AxisArray()

    Testing:

        pytest tests/core/test_axes.py openfisca_core/simulations/axis_array.py

    .. versionadded:: 3.4.0
    """

    axes: typing.Tuple[Axis, ...] = ()

    def append(self, tail: Axis) -> AxisArray:
        """
        Append an :class:`Axis` to our axes collection.

        Usage:

        >>> axis_array = AxisArray()
        >>> axis = Axis(name = "salary", count = 3, min = 0, max = 3000)
        >>> axis_array.append(axis)  # doctest: +ELLIPSIS
        AxisArray(Axis(name='salary', ...),)
        """
        return self.__class__(axes = (*self.axes, tail))

    def __contains__(self, item: Axis) -> bool:
        return item in self.axes

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}{repr(self.axes)}"
