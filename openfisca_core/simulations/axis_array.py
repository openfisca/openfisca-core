from __future__ import annotations

import dataclasses
from typing import Any, Callable, Iterator, List, NoReturn, Union

from . import Axis


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
        AxisArray[[]]

    Testing:

        pytest tests/core/test_axes.py openfisca_core/simulations/axis_array.py

    .. versionadded:: 35.4.0
    """

    axes: List[Union[AxisArray, Axis, list]] = \
        dataclasses \
        .field(default_factory = lambda: [[]])

    def __post_init__(self) -> None:
        axes = self.validate(isinstance, self.axes, list)

        for item in self.__flatten(axes):
            self.validate(isinstance, item, (AxisArray, Axis))

    def __contains__(self, item: Union[AxisArray, Axis]) -> bool:
        return item in self.axes

    def __iter__(self) -> Iterator:
        return (item for item in self.axes)

    def __len__(self) -> int:
        return len(self.axes)

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}{repr(self.axes)}"

    def first(self) -> Union[AxisArray, Axis, List]:
        """
        Retrieves the first axis from our axes collection.

        Usage:

            >>> axis_array = AxisArray()
            >>> axis_array.first()
            []

            >>> axis_array = AxisArray([])
            >>> axis_array.first()
            Traceback (most recent call last):
            TypeError: Expecting a non empty list, but [] given

            >>> axis = Axis(name = "salary", count = 3, min = 0, max = 3000)
            >>> node_array = AxisArray([axis])
            >>> node_array.first()
            Axis(name='salary', count=3, min=0, max=3000, period=None, index=0)

            >>> axis = Axis(name = "salary", count = 3, min = 0, max = 3000)
            >>> axis_array = AxisArray()
            >>> axis_array = axis_array.append_parallel(axis)
            >>> axis_array.first()
            AxisArray[Axis(name='salary', ..., index=0)]

        .. versionadded:: 35.4.0
        """
        self.validate(lambda item, _: item, self.axes, "a non empty list")
        return self.axes[0]

    def append_parallel(self, tail: Axis) -> Union[AxisArray, NoReturn]:
        """
        Append an :obj:`Axis` to the first dimension of our collection.

        We choose the language "append" instead of "add" as, in a pythonic
        context, "add" means "concatenate". Here, instead, we're "appending"
        and :obj:`Axis` to a dimension (the first one) of the collection.

        Args:

            tail:   An :obj:`Axis` to append to the first dimension of our
                    collection.

        Usage:

            >>> axis_array = AxisArray()
            >>> axis = Axis(name = "salary", count = 3, min = 0, max = 3000)
            >>> axis_array.append_parallel(axis)
            AxisArray[AxisArray[Axis(name='salary', ...)]]

        .. versionadded:: 35.4.0
        """
        parallel = self.validate(isinstance, self.first(), (AxisArray, list))
        appended = self.__append(parallel, tail)
        return self.__append(self.axes, appended)

    def validate(
            self,
            condition: Callable,
            real: Any,
            expected: Any,
            ) -> Union[Any, NoReturn]:
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

        .. versionadded:: 35.4.0
        """
        if condition(real, expected):
            return real

        raise TypeError(f"Expecting {expected}, but {real} given")

    def __append(
            self,
            axes: List[Union[AxisArray, Axis, list]],
            tail: Union[AxisArray, Axis],
            ) -> Union[AxisArray, NoReturn]:
        """
        Append an element to an array.

        Args:

            axes:   An :obj:`AxisArray` to be appended to.
            tail:   An :obj:`Axis` or an :obj:`AxisArray` to append.

        .. versionadded:: 35.4.0
        """
        self.validate(isinstance, axes, list)
        self.validate(isinstance, tail, (AxisArray, Axis))
        return self.__class__([*axes, tail][-1:])

    def __flatten(self, axes: list) -> List[Union[AxisArray, Axis]]:
        """
        Flatten out our entire collection.

        Args:

            axes:   Our collection.

        .. versionadded:: 35.4.0
        """
        if not axes:
            return axes

        if isinstance(axes[0], list):
            return self.__flatten(axes[0]) + self.__flatten(axes[1:])

        return axes[:1] + self.__flatten(axes[1:])
