from __future__ import annotations

import dataclasses
import typing

from .axis import Axis


@dataclasses.dataclass(frozen = True)
class AxisArray:
    """
    A collection of :obj:`Axis` and a bunch of business logic.

    Axis expansion is a feature in :module:`openfisca_core` that allows us to
    parametrise some dimensions in order to create and to evaluate a range of
    values for others.

    The most typical use of axis expansion is evaluate different numerical
    values, starting from a :attr:`min_` and up to a :attr:`max_`, that could
    take any given :class:`openfisca_core.variables.Variable` for any given
    :class:`openfisca_core.periods.Period` for any given population (or a
    collection of :module:`openfisca_core.entities`).

    Attributes:

        axes:   A :type:`list` containing our collection of :obj:`Axis`.

    Usage:

        >>> axis_array = AxisArray()
        >>> axis_array
        AxisArray[]

    Testing:

        pytest tests/core/test_axes.py openfisca_core/simulations/axis_array.py

    .. versionadded:: 3.4.0
    """

    axes: typing.List[Axis] = dataclasses.field(default_factory = list)

    def __post_init__(self) -> None:
        self.__is_list(self.axes)
        list(map(self.__is_axis, self.axes))

    def __contains__(self, item: Axis) -> bool:
        return item in self.axes

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}{repr(self.axes)}"

    def first(self) -> typing.Optional[Axis]:
        """
        Retrieves the first :obj:`Axis` from our axes collection.

        Usage:

            >>> axis_array = AxisArray()
            >>> not axis_array.first()
            True

            >>> axis = Axis(name = "salary", count = 3, min = 0, max = 3000)
            >>> axis_array = axis_array.append(axis)
            >>> axis_array.first()
            Axis(name='salary', ..., index=None)
        """
        if len(self.axes) == 0:
            return None

        return self.axes[0]

    def append(self, tail: Axis) -> typing.Union[AxisArray, typing.NoReturn]:
        """
        Append an :obj:`Axis` to our axes collection.

        Args:

            axis:   An :obj:`Axis` to append to our collection.

        Usage:

            >>> axis_array = AxisArray()
            >>> axis = Axis(name = "salary", count = 3, min = 0, max = 3000)
            >>> axis_array.append(axis)
            AxisArray[Axis(name='salary', ...)]
        """
        self.__is_axis(tail)
        return self.__class__(axes = [*self.axes, tail])

    def __is_list(self, axes: list) -> typing.Union[bool, typing.NoReturn]:
        if isinstance(axes, list):
            return True

        raise TypeError(f"Expecting a list, but {type(self.axes)} given")

    def __is_axis(self, item: Axis) -> typing.Union[bool, typing.NoReturn]:
        if isinstance(item, Axis):
            return True

        raise TypeError(f"Expecting an {Axis}, but {type(item)} given")
