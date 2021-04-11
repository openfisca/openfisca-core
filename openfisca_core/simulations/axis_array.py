from __future__ import annotations

import dataclasses
from typing import Any, Callable, List, NoReturn, Optional, Union

from .axis import Axis


@dataclasses.dataclass(frozen = True)
class AxisArray:
    """
    A collection of :obj:`Axis` (some business logic).

    Axis expansion is a feature in :module:`openfisca_core` that allows us to
    parametrise some dimensions in order to create and to evaluate a range of
    values for others.

    The most typical use of axis expansion is evaluate different numerical
    values, starting from a :attr:`min_` and up to a :attr:`max_`, that could
    take any given :class:`openfisca_core.variables.Variable` for any given
    :class:`openfisca_core.periods.Period` for any given population (or a
    collection of :module:`openfisca_core.entities`).

    As axes have a relative position relative to each other, they can be either
    equidistant, that is parallel, or perpendicular. We assume the first
    dimension to be a collection of parallel axes relative to themselves.

    Henceforward, we will consider each parallel axis as belonging to this
    first dimension, and each perpendicular axis as belonging to a new
    dimension, perpendicular to the previous one: that is, we won't be adding
    more than one axis for each perpendicular dimension beyond the first one.

    As you might've already guess, it is not possible to add any parallel or
    perpendicular axis relative to anything, so we assume the following when
    our collection is yet empty: whenever you add a parallel axis it will by
    default be added to the first dimension, and whenever you add a
    perpendicular axis it will be added in isolation to second dimension and
    beyond.

    Adding a perpendicular axis to an empty collection is a conceptual error
    so instead of trying to mitigate this, we will rather error out and let
    the user know why she can't do that and how she can correct they way she's
    building her collection of axes (simply put to add first a parallel axis).

    Attributes:

        axes:   A :type:`list` containing our collection of :obj:`Axis`.

    Usage:

        >>> axis_array = AxisArray()
        >>> axis_array
        AxisArray[]

    Testing:

        pytest tests/core/test_axes.py openfisca_core/simulations/axis_array.py

    .. versionadded:: 35.4.0
    """

    axes: List[Axis] = dataclasses.field(default_factory = list)

    def __post_init__(self) -> None:
        self.validate(isinstance, self.axes, list)

        for axis in self.axes:
            self.validate(isinstance, axis, Axis)

    def __contains__(self, item: Axis) -> bool:
        return item in self.axes

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}{repr(self.axes)}"

    def first(self) -> Optional[Axis]:
        """
        Retrieves the first :obj:`Axis` from our axes collection.

        Usage:

            >>> axis_array = AxisArray()
            >>> axis_array.first()
            Traceback (most recent call last):
            TypeError: Expecting a non empty list, but [] given

            >>> axis = Axis(name = "salary", count = 3, min = 0, max = 3000)
            >>> axis_array = axis_array.append(axis)
            >>> axis_array.first()
            Axis(name='salary', ..., index=0)
        """
        self.validate(lambda axes, _: axes, self.axes, "a non empty list")
        return self.axes[0]

    def append(self, tail: Axis) -> Union[AxisArray, NoReturn]:
        """
        Append an :obj:`Axis` to our axes collection.

        Args:

            tail:   An :obj:`Axis` to append to our collection.

        Usage:

            >>> axis_array = AxisArray()
            >>> axis = Axis(name = "salary", count = 3, min = 0, max = 3000)
            >>> axis_array.append(axis)
            AxisArray[Axis(name='salary', ...)]
        """
        self.validate(isinstance, tail, Axis)
        return self.__class__(axes = [*self.axes, tail])

    def validate(
            self,
            condition: Callable,
            real: Any,
            expected: Any,
            ) -> Union[bool, NoReturn]:
        """
        Validate that a condition holds true.

        Args:

            condition:  A function reprensenting the condition to validate.
            real:       The value given as input, passed to :args:`condition`.
            expected:   The value we expect, passed to :args:`condition`.

        Usage:

            >>> axis_array = AxisArray()
            >>> condition = isinstance
            >>> real = tuple()
            >>> expected = list
            >>> axis_array.validate(condition, real, expected)
            Traceback (most recent call last):
            TypeError: Expecting <class 'list'>, but () given
        """
        if condition(real, expected):
            return True

        raise TypeError(f"Expecting {expected}, but {real} given")
