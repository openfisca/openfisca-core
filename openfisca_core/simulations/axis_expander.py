from __future__ import annotations

import functools
import typing

if typing.TYPE_CHECKING:
    from . import AxisArray


class AxisExpander:
    """
    Expander of all axes for a given axes collection (lots of domain logic).

    Axis expansion is a feature in :module:`openfisca_core` that allows us to
    parametrise some dimensions in order to create and to evaluate a range of
    values for others.

    The most typical use of axis expansion is evaluate different numerical
    values, starting from a :attr:`min_` and up to a :attr:`max_`, that could
    take any given :class:`openfisca_core.variables.Variable` for any given
    :class:`openfisca_core.periods.Period` for any given population (or a
    collection of :module:`openfisca_core.entities`).

    Args:

        axis_array: An array of axes to expand.

    .. versionadded:: 35.4.0
    """

    def __init__(self, axis_array: AxisArray) -> None:
        self.__axis_array = axis_array

    @property
    def axis_array(self) -> AxisArray:
        """
        An array of axes to expand.

        .. versionadded:: 35.4.0
        """
        return self.__axis_array

    def count_cells(self):
        """
        Count the total number of cells on an axes collection.

        As a collection of axes is comprised of several perpendicular
        collections of axes, relative to each other, we're going to consider
        the total number of cells as being the multiplication of the value
        :attr:`Axis.count` for the first axis of each dimension.

        We assume however that all parallel axes should have the same count.
        This method searches for a compatible axis (the first one). If none
        exists, it should error out (we do not check here at it is the
        responsability of :class:`AxisArray` to do so: data integrity is a
        domain invariant related to the data model).

        Usage:

        >>> from . import Axis, AxisArray
        >>> axis = Axis(name = "salary", count = 3, min = 0, max = 3000)
        >>> axis_array = AxisArray()
        >>> axis_array = axis_array.add_parallel(axis)
        >>> axis_array = axis_array.add_perpendicular(axis)
        >>> axis_expander = AxisExpander(axis_array)
        >>> axis_expander.count_cells()
        9

        .. versionadded:: 35.4.0
        """
        axis_count = map(lambda dim: dim.first().count, self.axis_array)
        return functools.reduce(lambda acc, count: acc * count, axis_count, 1)
