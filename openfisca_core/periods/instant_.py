from __future__ import annotations

import dataclasses
import datetime
import functools
from typing import Any, Iterator, Tuple, Union

from typing_extensions import Literal

from dateutil import relativedelta

from openfisca_core import commons, periods
from openfisca_core.types import SupportsPeriod

from .date_unit import DateUnit

DateLike = Tuple[int, ...]
DateKeys = Literal[DateUnit.YEAR, DateUnit.MONTH, DateUnit.DAY]
OffsetBy = Union[Literal["first-of", "last-of"], int]


@dataclasses.dataclass(init = False, frozen = True)
class Instant:
    """An instant in time (year, month, day).

    An :class:`.Instant` represents the most atomic and indivisible unit time
    of a legislations.

    Current implementation considers this unit to be a day, so
    :obj:`instants <.Instant>` can be thought of as "day dates".

    Attributes:
        year (:obj:`int`):
            The year of the :obj:`.Instant`.
        month (:obj:`int`):
            The month of the :obj:`.Instant`.
        day (:obj:`int`):
            The day of the :obj:`.Instant.`
        date (:obj:`datetime.date`:):
            The converted :obj:`.Instant`.
        canonical (tuple(int, int, int)):
            The ``year``, ``month``, and ``day``, accordingly.

    Args:
        units (tuple(int, int, int)):
            The ``year``, ``month``, and ``day``, accordingly.

    Examples:
        >>> instant = Instant((2021, 9, 13))

        >>> repr(Instant)
        "<class 'openfisca_core.periods.instant_.Instant'>"

        >>> repr(instant)
        '<Instant(2021, 9, 13)>'

        >>> str(instant)
        '2021-09-13'

        >>> dict([(instant, (2021, 9, 13))])
        {<Instant(2021, 9, 13)>: (2021, 9, 13)}

        >>> tuple(instant)
        (2021, 9, 13)

        >>> instant[0]
        2021

        >>> instant[0] in instant
        True

        >>> len(instant)
        3

        >>> instant == (2021, 9, 13)
        True

        >>> instant != (2021, 9, 13)
        False

        >>> instant > (2020, 9, 13)
        True

        >>> instant < (2020, 9, 13)
        False

        >>> instant >= (2020, 9, 13)
        True

        >>> instant <= (2020, 9, 13)
        False

        >>> instant.year
        2021

        >>> instant.month
        9

        >>> instant.day
        13

        >>> instant.canonical
        (2021, 9, 13)

        >>> instant.date
        datetime.date(2021, 9, 13)

        >>> year, month, day = instant

    """

    __slots__ = ["year", "month", "day", "date", "canonical"]
    year: int
    month: int
    day: int
    date: datetime.date
    canonical: DateLike

    def __init__(self, units: DateLike) -> None:
        year, month, day = units
        object.__setattr__(self, "year", year)
        object.__setattr__(self, "month", month)
        object.__setattr__(self, "day", day)
        object.__setattr__(self, "date", periods.DATE(year, month, day))
        object.__setattr__(self, "canonical", units)

    def __repr__(self) -> str:
        return \
            f"<{self.__class__.__name__}" \
            f"({self.year}, {self.month}, {self.day})>"

    @functools.lru_cache(maxsize = None)
    def __str__(self) -> str:
        return self.date.isoformat()

    def __contains__(self, item: Any) -> bool:
        return item in self.canonical

    def __getitem__(self, key: int) -> int:
        return self.canonical[key]

    def __iter__(self) -> Iterator[int]:
        return iter(self.canonical)

    def __len__(self) -> int:
        return len(self.canonical)

    def __eq__(self, other: Any) -> bool:
        return self.canonical == other

    def __ne__(self, other: Any) -> bool:
        return self.canonical != other

    def __lt__(self, other: Any) -> bool:
        return self.canonical < other

    def __le__(self, other: Any) -> bool:
        return self.canonical <= other

    def __gt__(self, other: Any) -> bool:
        return self.canonical > other

    def __ge__(self, other: Any) -> bool:
        return self.canonical >= other

    @commons.deprecated(since = "35.9.0", expires = "the future")
    def period(self, unit: DateUnit, size: int = 1) -> SupportsPeriod:
        """Creates a new :obj:`.Period` starting at :obj:`.Instant`.

        Args:
            unit: ``day`` or ``month`` or ``year``.
            size: How many of ``unit``.

        Returns:
            A new object :obj:`.Period`.

        Raises:
            :exc:`AssertionError`: When ``unit`` is not a date unit.
            :exc:`AssertionError`: When ``size`` is not an unsigned :obj:`int`.

        Examples:
            >>> Instant((2021, 9, 13)).period(DateUnit.YEAR.value)
            <Period(('year', <Instant(2021, 9, 13)>, 1))>

            >>> Instant((2021, 9, 13)).period("month", 2)
            <Period(('month', <Instant(2021, 9, 13)>, 2))>

        .. deprecated:: 35.9.0
            :meth:`.period` has been deprecated and will be removed in the
            future. The functionality is now provided by :func:`.period`.

        """

        assert unit in DateUnit.ethereal, \
            f"Invalid unit: {unit} of type {type(unit)}. Expecting any of " \
            f"{', '.join(str(unit) for unit in DateUnit.ethereal)}."

        assert isinstance(size, int) and size >= 1, \
            f"Invalid size: {size} of type {type(size)}. Expecting any " \
            "int >= 1."

        if isinstance(unit, str):
            unit = DateUnit[unit]

        return periods.period(f"{unit.value}:{str(self)}:{size}")

    @functools.lru_cache(maxsize = None)
    def offset(self, offset: OffsetBy, unit: DateUnit) -> Instant:
        """Increments/decrements the given instant with offset units.

        Args:
            offset: How much of ``unit`` to offset.
            unit: What to offset

        Returns:
            :obj:`.Instant`: A new :obj:`.Instant` in time.

        Raises:
            :exc:`AssertionError`: When ``unit`` is not a date unit.
            :exc:`AssertionError`: When ``offset`` is not either ``first-of``,
                ``last-of``, or any :obj:`int`.

        Examples:
            >>> Instant((2020, 12, 31)).offset("first-of", DateUnit.MONTH.value)
            <Instant(2020, 12, 1)>

            >>> Instant((2020, 1, 1)).offset("last-of", "year")
            <Instant(2020, 12, 31)>

            >>> Instant((2020, 1, 1)).offset(1, DateUnit.YEAR.value)
            <Instant(2021, 1, 1)>

            >>> Instant((2020, 1, 1)).offset(-3, "day")
            <Instant(2019, 12, 29)>

        """

        #: Use current ``year`` fro the offset.
        year = self.year

        #: Use current ``month`` fro the offset.
        month = self.month

        #: Use current ``day`` fro the offset.
        day = self.day

        assert unit in DateUnit.ethereal, \
            f"Invalid unit: {unit} of type {type(unit)}. Expecting any of " \
            f"{', '.join(str(unit) for unit in DateUnit.ethereal)}."

        if offset == "first-of" and unit == DateUnit.YEAR:
            return self.__class__((year, 1, 1))

        if offset == "first-of" and unit == DateUnit.MONTH:
            return self.__class__((year, month, 1))

        if offset == "last-of" and unit == DateUnit.YEAR:
            return self.__class__((year, 12, 31))

        if offset == "last-of" and unit == DateUnit.MONTH:
            day = periods.LAST(year, month)[1]
            return self.__class__((year, month, day))

        assert isinstance(offset, int), \
            f"Invalid offset: {offset} of type {type(offset)}. Expecting " \
            "any int."

        if unit == DateUnit.YEAR:
            date = self.date + relativedelta.relativedelta(years = offset)
            return self.__class__((date.year, date.month, date.day))

        if unit == DateUnit.MONTH:
            date = self.date + relativedelta.relativedelta(months = offset)
            return self.__class__((date.year, date.month, date.day))

        if unit == DateUnit.DAY:
            date = self.date + relativedelta.relativedelta(days = offset)
            return self.__class__((date.year, date.month, date.day))

        return self
