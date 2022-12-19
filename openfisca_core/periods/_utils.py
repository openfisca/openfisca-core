from __future__ import annotations

from typing import Callable

from pendulum.datetime import Date


def add(date: Date, unit: str, count: int) -> Date:
    """Add ``count`` ``unit``s to a ``date``.

    Args:
        date: The date to add to.
        unit: The unit to add.
        count: The number of units to add.

    Returns:
        A new Date.

    Examples:
        >>> add(Date(2022, 1, 1), "years", 1)
        Date(2023, 1, 1)

    .. versionadded:: 39.0.0

    """

    fun: Callable[..., Date] = date.add

    new: Date = fun(**{unit: count})

    return new
