from __future__ import annotations

from collections.abc import Sequence

import calendar
import datetime

import pendulum

from . import helpers, types as t
from .date_unit import DateUnit
from .instant_ import Instant


class Period(tuple[t.DateUnit, t.Instant, int]):
    """Toolbox to handle date intervals.

    A :class:`.Period` is a triple (``unit``, ``start``, ``size``).

    Attributes:
        unit (:obj:`str`):
            Either ``year``, ``month``, ``day`` or ``eternity``.
        start (:obj:`.Instant`):
            The "instant" the :obj:`.Period` starts at.
        size (:obj:`int`):
            The amount of ``unit``, starting at ``start``, at least ``1``.

    Args:
        (tuple(tuple(str, .Instant, int))):
            The ``unit``, ``start``, and ``size``, accordingly.

    Examples:
        >>> instant = Instant((2021, 10, 1))
        >>> period = Period((DateUnit.YEAR, instant, 3))

        >>> repr(Period)
        "<class 'openfisca_core.periods.period_.Period'>"

        >>> repr(period)
        "Period((<DateUnit.YEAR: 'year'>, Instant((2021, 10, 1)), 3))"

        >>> str(period)
        'year:2021-10:3'

        >>> dict([period, instant])
        Traceback (most recent call last):
        ValueError: dictionary update sequence element #0 has length 3...

        >>> list(period)
        [<DateUnit.YEAR: 'year'>, Instant((2021, 10, 1)), 3]

        >>> period[0]
        <DateUnit.YEAR: 'year'>

        >>> period[0] in period
        True

        >>> len(period)
        3

        >>> period == Period((DateUnit.YEAR, instant, 3))
        True

        >>> period != Period((DateUnit.YEAR, instant, 3))
        False

        >>> period > Period((DateUnit.YEAR, instant, 3))
        False

        >>> period < Period((DateUnit.YEAR, instant, 3))
        False

        >>> period >= Period((DateUnit.YEAR, instant, 3))
        True

        >>> period <= Period((DateUnit.YEAR, instant, 3))
        True

        >>> period.days
        1096

        >>> period.size_in_months
        36

        >>> period.size_in_days
        1096

        >>> period.stop
        Instant((2024, 9, 30))

        >>> period.unit
        <DateUnit.YEAR: 'year'>

        >>> period.last_3_months
        Period((<DateUnit.MONTH: 'month'>, Instant((2021, 7, 1)), 3))

        >>> period.last_month
        Period((<DateUnit.MONTH: 'month'>, Instant((2021, 9, 1)), 1))

        >>> period.last_year
        Period((<DateUnit.YEAR: 'year'>, Instant((2020, 1, 1)), 1))

        >>> period.n_2
        Period((<DateUnit.YEAR: 'year'>, Instant((2019, 1, 1)), 1))

        >>> period.this_year
        Period((<DateUnit.YEAR: 'year'>, Instant((2021, 1, 1)), 1))

        >>> period.first_month
        Period((<DateUnit.MONTH: 'month'>, Instant((2021, 10, 1)), 1))

        >>> period.first_day
        Period((<DateUnit.DAY: 'day'>, Instant((2021, 10, 1)), 1))


    Since a period is a triple it can be used as a dictionary key.

    """

    __slots__ = ()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({super().__repr__()})"

    def __str__(self) -> t.PeriodStr:
        unit, start_instant, size = self

        if unit == DateUnit.ETERNITY:
            return t.PeriodStr(unit.upper())

        # ISO format date units.
        f_year, month, day = start_instant

        # ISO calendar date units.
        c_year, week, weekday = datetime.date(f_year, month, day).isocalendar()

        # 1 year long period
        if unit == DateUnit.MONTH and size == 12 or unit == DateUnit.YEAR and size == 1:
            if month == 1:
                # civil year starting from january
                return t.PeriodStr(str(f_year))
            # rolling year
            return t.PeriodStr(f"{DateUnit.YEAR}:{f_year}-{month:02d}")

        # simple month
        if unit == DateUnit.MONTH and size == 1:
            return t.PeriodStr(f"{f_year}-{month:02d}")

        # several civil years
        if unit == DateUnit.YEAR and month == 1:
            return t.PeriodStr(f"{unit}:{f_year}:{size}")

        if unit == DateUnit.DAY:
            if size == 1:
                return t.PeriodStr(f"{f_year}-{month:02d}-{day:02d}")
            return t.PeriodStr(f"{unit}:{f_year}-{month:02d}-{day:02d}:{size}")

        # 1 week
        if unit == DateUnit.WEEK and size == 1:
            if week < 10:
                return t.PeriodStr(f"{c_year}-W0{week}")

            return t.PeriodStr(f"{c_year}-W{week}")

        # several weeks
        if unit == DateUnit.WEEK and size > 1:
            if week < 10:
                return t.PeriodStr(f"{unit}:{c_year}-W0{week}:{size}")

            return t.PeriodStr(f"{unit}:{c_year}-W{week}:{size}")

        # 1 weekday
        if unit == DateUnit.WEEKDAY and size == 1:
            if week < 10:
                return t.PeriodStr(f"{c_year}-W0{week}-{weekday}")

            return t.PeriodStr(f"{c_year}-W{week}-{weekday}")

        # several weekdays
        if unit == DateUnit.WEEKDAY and size > 1:
            if week < 10:
                return t.PeriodStr(f"{unit}:{c_year}-W0{week}-{weekday}:{size}")

            return t.PeriodStr(f"{unit}:{c_year}-W{week}-{weekday}:{size}")

        # complex period
        return t.PeriodStr(f"{unit}:{f_year}-{month:02d}:{size}")

    @property
    def unit(self) -> t.DateUnit:
        """The ``unit`` of the ``Period``.

        Example:
            >>> instant = Instant((2021, 10, 1))
            >>> period = Period((DateUnit.YEAR, instant, 3))
            >>> period.unit
            <DateUnit.YEAR: 'year'>

        """
        return self[0]

    @property
    def start(self) -> t.Instant:
        """The ``Instant`` at which the ``Period`` starts.

        Example:
            >>> instant = Instant((2021, 10, 1))
            >>> period = Period((DateUnit.YEAR, instant, 3))
            >>> period.start
            Instant((2021, 10, 1))

        """
        return self[1]

    @property
    def size(self) -> int:
        """The ``size`` of the ``Period``.

        Example:
            >>> instant = Instant((2021, 10, 1))
            >>> period = Period((DateUnit.YEAR, instant, 3))
            >>> period.size
            3

        """
        return self[2]

    @property
    def date(self) -> pendulum.Date:
        """The date representation of the ``Period`` start date.

        Examples:
            >>> instant = Instant((2021, 10, 1))

            >>> period = Period((DateUnit.YEAR, instant, 1))
            >>> period.date
            Date(2021, 10, 1)

            >>> period = Period((DateUnit.YEAR, instant, 3))
            >>> period.date
            Traceback (most recent call last):
            ValueError: "date" is undefined for a period of size > 1: year:2021-10:3.

        """
        if self.size != 1:
            msg = f'"date" is undefined for a period of size > 1: {self}.'
            raise ValueError(msg)

        return self.start.date

    @property
    def size_in_years(self) -> int:
        """The ``size`` of the ``Period`` in years.

        Examples:
            >>> instant = Instant((2021, 10, 1))

            >>> period = Period((DateUnit.YEAR, instant, 3))
            >>> period.size_in_years
            3

            >>> period = Period((DateUnit.MONTH, instant, 3))
            >>> period.size_in_years
            Traceback (most recent call last):
            ValueError: Can't calculate number of years in a month.

        """
        if self.unit == DateUnit.YEAR:
            return self.size

        msg = f"Can't calculate number of years in a {self.unit}."
        raise ValueError(msg)

    @property
    def size_in_months(self) -> int:
        """The ``size`` of the ``Period`` in months.

        Examples:
            >>> instant = Instant((2021, 10, 1))

            >>> period = Period((DateUnit.YEAR, instant, 3))
            >>> period.size_in_months
            36

            >>> period = Period((DateUnit.DAY, instant, 3))
            >>> period.size_in_months
            Traceback (most recent call last):
            ValueError: Can't calculate number of months in a day.

        """
        if self.unit == DateUnit.YEAR:
            return self.size * 12

        if self.unit == DateUnit.MONTH:
            return self.size

        msg = f"Can't calculate number of months in a {self.unit}."
        raise ValueError(msg)

    @property
    def size_in_days(self) -> int:
        """The ``size`` of the ``Period`` in days.

        Examples:
            >>> instant = Instant((2019, 10, 1))

            >>> period = Period((DateUnit.YEAR, instant, 3))
            >>> period.size_in_days
            1096

            >>> period = Period((DateUnit.MONTH, instant, 3))
            >>> period.size_in_days
            92

        """
        if self.unit in (DateUnit.YEAR, DateUnit.MONTH):
            last = self.start.offset(self.size, self.unit)
            if last is None:
                raise NotImplementedError
            last_day = last.offset(-1, DateUnit.DAY)
            if last_day is None:
                raise NotImplementedError
            return (last_day.date - self.start.date).days + 1

        if self.unit == DateUnit.WEEK:
            return self.size * 7

        if self.unit in (DateUnit.DAY, DateUnit.WEEKDAY):
            return self.size

        msg = f"Can't calculate number of days in a {self.unit}."
        raise ValueError(msg)

    @property
    def size_in_weeks(self) -> int:
        """The ``size`` of the ``Period`` in weeks.

        Examples:
            >>> instant = Instant((2019, 10, 1))

            >>> period = Period((DateUnit.YEAR, instant, 3))
            >>> period.size_in_weeks
            156

            >>> period = Period((DateUnit.YEAR, instant, 5))
            >>> period.size_in_weeks
            261

        """
        if self.unit == DateUnit.YEAR:
            start = self.start.date
            cease = start.add(years=self.size)
            delta = start.diff(cease)
            return delta.in_weeks()

        if self.unit == DateUnit.MONTH:
            start = self.start.date
            cease = start.add(months=self.size)
            delta = start.diff(cease)
            return delta.in_weeks()

        if self.unit == DateUnit.WEEK:
            return self.size

        msg = f"Can't calculate number of weeks in a {self.unit}."
        raise ValueError(msg)

    @property
    def size_in_weekdays(self) -> int:
        """The ``size`` of the ``Period`` in weekdays.

        Examples:
            >>> instant = Instant((2019, 10, 1))

            >>> period = Period((DateUnit.YEAR, instant, 3))
            >>> period.size_in_weekdays
            1092

            >>> period = Period((DateUnit.WEEK, instant, 3))
            >>> period.size_in_weekdays
            21

        """
        if self.unit == DateUnit.YEAR:
            return self.size_in_weeks * 7

        if DateUnit.MONTH in self.unit:
            last = self.start.offset(self.size, self.unit)
            if last is None:
                raise NotImplementedError
            last_day = last.offset(-1, DateUnit.DAY)
            if last_day is None:
                raise NotImplementedError
            return (last_day.date - self.start.date).days + 1

        if self.unit == DateUnit.WEEK:
            return self.size * 7

        if self.unit in (DateUnit.DAY, DateUnit.WEEKDAY):
            return self.size

        msg = f"Can't calculate number of weekdays in a {self.unit}."
        raise ValueError(msg)

    @property
    def days(self) -> int:
        """Same as ``size_in_days``."""
        return (self.stop.date - self.start.date).days + 1

    def intersection(
        self, start: t.Instant | None, stop: t.Instant | None
    ) -> t.Period | None:
        if start is None and stop is None:
            return self
        period_start = self[1]
        period_stop = self.stop
        if start is None:
            start = period_start
        if stop is None:
            stop = period_stop
        if stop < period_start or period_stop < start:
            return None
        intersection_start = max(period_start, start)
        intersection_stop = min(period_stop, stop)
        if intersection_start == period_start and intersection_stop == period_stop:
            return self
        if (
            intersection_start.day == 1
            and intersection_start.month == 1
            and intersection_stop.day == 31
            and intersection_stop.month == 12
        ):
            return self.__class__(
                (
                    DateUnit.YEAR,
                    intersection_start,
                    intersection_stop.year - intersection_start.year + 1,
                ),
            )
        if (
            intersection_start.day == 1
            and intersection_stop.day
            == calendar.monthrange(intersection_stop.year, intersection_stop.month)[1]
        ):
            return self.__class__(
                (
                    DateUnit.MONTH,
                    intersection_start,
                    (
                        (intersection_stop.year - intersection_start.year) * 12
                        + intersection_stop.month
                        - intersection_start.month
                        + 1
                    ),
                ),
            )
        return self.__class__(
            (
                DateUnit.DAY,
                intersection_start,
                (intersection_stop.date - intersection_start.date).days + 1,
            ),
        )

    def get_subperiods(self, unit: t.DateUnit) -> Sequence[t.Period]:
        """Return the list of periods of unit ``unit`` contained in self.

        Examples:
            >>> period = Period((DateUnit.YEAR, Instant((2021, 1, 1)), 1))
            >>> period.get_subperiods(DateUnit.MONTH)
            [Period((<DateUnit.MONTH: 'month'>, Instant((2021, 1, 1)), 1)),...]

            >>> period = Period((DateUnit.YEAR, Instant((2021, 1, 1)), 2))
            >>> period.get_subperiods(DateUnit.YEAR)
            [Period((<DateUnit.YEAR: 'year'>, Instant((2021, 1, 1)), 1)), P...]

        """
        if helpers.unit_weight(self.unit) < helpers.unit_weight(unit):
            msg = f"Cannot subdivide {self.unit} into {unit}"
            raise ValueError(msg)

        if unit == DateUnit.YEAR:
            return [self.this_year.offset(i, DateUnit.YEAR) for i in range(self.size)]

        if unit == DateUnit.MONTH:
            return [
                self.first_month.offset(i, DateUnit.MONTH)
                for i in range(self.size_in_months)
            ]

        if unit == DateUnit.DAY:
            return [
                self.first_day.offset(i, DateUnit.DAY) for i in range(self.size_in_days)
            ]

        if unit == DateUnit.WEEK:
            return [
                self.first_week.offset(i, DateUnit.WEEK)
                for i in range(self.size_in_weeks)
            ]

        if unit == DateUnit.WEEKDAY:
            return [
                self.first_weekday.offset(i, DateUnit.WEEKDAY)
                for i in range(self.size_in_weekdays)
            ]

        msg = f"Cannot subdivide {self.unit} into {unit}"
        raise ValueError(msg)

    def offset(self, offset: str | int, unit: t.DateUnit | None = None) -> t.Period:
        """Increment (or decrement) the given period with offset units.

        Examples:
            >>> Period((DateUnit.DAY, Instant((2021, 1, 1)), 365)).offset(1)
            Period((<DateUnit.DAY: 'day'>, Instant((2021, 1, 2)), 365))

            >>> Period((DateUnit.DAY, Instant((2021, 1, 1)), 365)).offset(
            ...     1, DateUnit.DAY
            ... )
            Period((<DateUnit.DAY: 'day'>, Instant((2021, 1, 2)), 365))

            >>> Period((DateUnit.DAY, Instant((2021, 1, 1)), 365)).offset(
            ...     1, DateUnit.MONTH
            ... )
            Period((<DateUnit.DAY: 'day'>, Instant((2021, 2, 1)), 365))

            >>> Period((DateUnit.DAY, Instant((2021, 1, 1)), 365)).offset(
            ...     1, DateUnit.YEAR
            ... )
            Period((<DateUnit.DAY: 'day'>, Instant((2022, 1, 1)), 365))

            >>> Period((DateUnit.MONTH, Instant((2021, 1, 1)), 12)).offset(1)
            Period((<DateUnit.MONTH: 'month'>, Instant((2021, 2, 1)), 12))

            >>> Period((DateUnit.MONTH, Instant((2021, 1, 1)), 12)).offset(
            ...     1, DateUnit.DAY
            ... )
            Period((<DateUnit.MONTH: 'month'>, Instant((2021, 1, 2)), 12))

            >>> Period((DateUnit.MONTH, Instant((2021, 1, 1)), 12)).offset(
            ...     1, DateUnit.MONTH
            ... )
            Period((<DateUnit.MONTH: 'month'>, Instant((2021, 2, 1)), 12))

            >>> Period((DateUnit.MONTH, Instant((2021, 1, 1)), 12)).offset(
            ...     1, DateUnit.YEAR
            ... )
            Period((<DateUnit.MONTH: 'month'>, Instant((2022, 1, 1)), 12))

            >>> Period((DateUnit.YEAR, Instant((2021, 1, 1)), 1)).offset(1)
            Period((<DateUnit.YEAR: 'year'>, Instant((2022, 1, 1)), 1))

            >>> Period((DateUnit.YEAR, Instant((2021, 1, 1)), 1)).offset(
            ...     1, DateUnit.DAY
            ... )
            Period((<DateUnit.YEAR: 'year'>, Instant((2021, 1, 2)), 1))

            >>> Period((DateUnit.YEAR, Instant((2021, 1, 1)), 1)).offset(
            ...     1, DateUnit.MONTH
            ... )
            Period((<DateUnit.YEAR: 'year'>, Instant((2021, 2, 1)), 1))

            >>> Period((DateUnit.YEAR, Instant((2021, 1, 1)), 1)).offset(
            ...     1, DateUnit.YEAR
            ... )
            Period((<DateUnit.YEAR: 'year'>, Instant((2022, 1, 1)), 1))

            >>> Period((DateUnit.DAY, Instant((2011, 2, 28)), 1)).offset(1)
            Period((<DateUnit.DAY: 'day'>, Instant((2011, 3, 1)), 1))

            >>> Period((DateUnit.MONTH, Instant((2011, 2, 28)), 1)).offset(1)
            Period((<DateUnit.MONTH: 'month'>, Instant((2011, 3, 28)), 1))

            >>> Period((DateUnit.YEAR, Instant((2011, 2, 28)), 1)).offset(1)
            Period((<DateUnit.YEAR: 'year'>, Instant((2012, 2, 28)), 1))

            >>> Period((DateUnit.DAY, Instant((2011, 3, 1)), 1)).offset(-1)
            Period((<DateUnit.DAY: 'day'>, Instant((2011, 2, 28)), 1))

            >>> Period((DateUnit.MONTH, Instant((2011, 3, 1)), 1)).offset(-1)
            Period((<DateUnit.MONTH: 'month'>, Instant((2011, 2, 1)), 1))

            >>> Period((DateUnit.YEAR, Instant((2011, 3, 1)), 1)).offset(-1)
            Period((<DateUnit.YEAR: 'year'>, Instant((2010, 3, 1)), 1))

            >>> Period((DateUnit.DAY, Instant((2014, 1, 30)), 1)).offset(3)
            Period((<DateUnit.DAY: 'day'>, Instant((2014, 2, 2)), 1))

            >>> Period((DateUnit.MONTH, Instant((2014, 1, 30)), 1)).offset(3)
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 4, 30)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 1, 30)), 1)).offset(3)
            Period((<DateUnit.YEAR: 'year'>, Instant((2017, 1, 30)), 1))

            >>> Period((DateUnit.DAY, Instant((2021, 1, 1)), 365)).offset(-3)
            Period((<DateUnit.DAY: 'day'>, Instant((2020, 12, 29)), 365))

            >>> Period((DateUnit.MONTH, Instant((2021, 1, 1)), 12)).offset(-3)
            Period((<DateUnit.MONTH: 'month'>, Instant((2020, 10, 1)), 12))

            >>> Period((DateUnit.YEAR, Instant((2014, 1, 1)), 1)).offset(-3)
            Period((<DateUnit.YEAR: 'year'>, Instant((2011, 1, 1)), 1))

            >>> Period((DateUnit.DAY, Instant((2014, 2, 3)), 1)).offset(
            ...     "first-of", DateUnit.MONTH
            ... )
            Period((<DateUnit.DAY: 'day'>, Instant((2014, 2, 1)), 1))

            >>> Period((DateUnit.DAY, Instant((2014, 2, 3)), 1)).offset(
            ...     "first-of", DateUnit.YEAR
            ... )
            Period((<DateUnit.DAY: 'day'>, Instant((2014, 1, 1)), 1))

            >>> Period((DateUnit.DAY, Instant((2014, 2, 3)), 4)).offset(
            ...     "first-of", DateUnit.MONTH
            ... )
            Period((<DateUnit.DAY: 'day'>, Instant((2014, 2, 1)), 4))

            >>> Period((DateUnit.DAY, Instant((2014, 2, 3)), 4)).offset(
            ...     "first-of", DateUnit.YEAR
            ... )
            Period((<DateUnit.DAY: 'day'>, Instant((2014, 1, 1)), 4))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 1)).offset("first-of")
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 2, 1)), 1))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 1)).offset(
            ...     "first-of", DateUnit.MONTH
            ... )
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 2, 1)), 1))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 1)).offset(
            ...     "first-of", DateUnit.YEAR
            ... )
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 1, 1)), 1))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 4)).offset("first-of")
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 2, 1)), 4))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 4)).offset(
            ...     "first-of", DateUnit.MONTH
            ... )
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 2, 1)), 4))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 4)).offset(
            ...     "first-of", DateUnit.YEAR
            ... )
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 1, 1)), 4))

            >>> Period((DateUnit.YEAR, Instant((2014, 1, 30)), 1)).offset("first-of")
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 1, 1)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 1, 30)), 1)).offset(
            ...     "first-of", DateUnit.MONTH
            ... )
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 1, 1)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 1, 30)), 1)).offset(
            ...     "first-of", DateUnit.YEAR
            ... )
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 1, 1)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 2, 3)), 1)).offset("first-of")
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 1, 1)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 2, 3)), 1)).offset(
            ...     "first-of", DateUnit.MONTH
            ... )
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 2, 1)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 2, 3)), 1)).offset(
            ...     "first-of", DateUnit.YEAR
            ... )
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 1, 1)), 1))

            >>> Period((DateUnit.DAY, Instant((2014, 2, 3)), 1)).offset(
            ...     "last-of", DateUnit.MONTH
            ... )
            Period((<DateUnit.DAY: 'day'>, Instant((2014, 2, 28)), 1))

            >>> Period((DateUnit.DAY, Instant((2014, 2, 3)), 1)).offset(
            ...     "last-of", DateUnit.YEAR
            ... )
            Period((<DateUnit.DAY: 'day'>, Instant((2014, 12, 31)), 1))

            >>> Period((DateUnit.DAY, Instant((2014, 2, 3)), 4)).offset(
            ...     "last-of", DateUnit.MONTH
            ... )
            Period((<DateUnit.DAY: 'day'>, Instant((2014, 2, 28)), 4))

            >>> Period((DateUnit.DAY, Instant((2014, 2, 3)), 4)).offset(
            ...     "last-of", DateUnit.YEAR
            ... )
            Period((<DateUnit.DAY: 'day'>, Instant((2014, 12, 31)), 4))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 1)).offset("last-of")
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 2, 28)), 1))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 1)).offset(
            ...     "last-of", DateUnit.MONTH
            ... )
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 2, 28)), 1))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 1)).offset(
            ...     "last-of", DateUnit.YEAR
            ... )
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 12, 31)), 1))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 4)).offset("last-of")
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 2, 28)), 4))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 4)).offset(
            ...     "last-of", DateUnit.MONTH
            ... )
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 2, 28)), 4))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 4)).offset(
            ...     "last-of", DateUnit.YEAR
            ... )
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 12, 31)), 4))

            >>> Period((DateUnit.YEAR, Instant((2014, 2, 3)), 1)).offset("last-of")
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 12, 31)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 1, 1)), 1)).offset(
            ...     "last-of", DateUnit.MONTH
            ... )
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 1, 31)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 2, 3)), 1)).offset(
            ...     "last-of", DateUnit.YEAR
            ... )
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 12, 31)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 2, 3)), 1)).offset("last-of")
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 12, 31)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 2, 3)), 1)).offset(
            ...     "last-of", DateUnit.MONTH
            ... )
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 2, 28)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 2, 3)), 1)).offset(
            ...     "last-of", DateUnit.YEAR
            ... )
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 12, 31)), 1))

        """

        start: None | t.Instant = self[1].offset(
            offset, self[0] if unit is None else unit
        )

        if start is None:
            raise NotImplementedError

        return self.__class__(
            (
                self[0],
                start,
                self[2],
            ),
        )

    def contains(self, other: t.Period) -> bool:
        """Returns ``True`` if the period contains ``other``.

        For instance, ``period(2015)`` contains ``period(2015-01)``.

        """
        return self.start <= other.start and self.stop >= other.stop

    @property
    def stop(self) -> t.Instant:
        """Return the last day of the period as an Instant instance.

        Examples:
            >>> Period((DateUnit.YEAR, Instant((2022, 1, 1)), 1)).stop
            Instant((2022, 12, 31))

            >>> Period((DateUnit.MONTH, Instant((2022, 1, 1)), 12)).stop
            Instant((2022, 12, 31))

            >>> Period((DateUnit.DAY, Instant((2022, 1, 1)), 365)).stop
            Instant((2022, 12, 31))

            >>> Period((DateUnit.YEAR, Instant((2012, 2, 29)), 1)).stop
            Instant((2013, 2, 27))

            >>> Period((DateUnit.MONTH, Instant((2012, 2, 29)), 1)).stop
            Instant((2012, 3, 28))

            >>> Period((DateUnit.DAY, Instant((2012, 2, 29)), 1)).stop
            Instant((2012, 2, 29))

            >>> Period((DateUnit.YEAR, Instant((2012, 2, 29)), 2)).stop
            Instant((2014, 2, 27))

            >>> Period((DateUnit.MONTH, Instant((2012, 2, 29)), 2)).stop
            Instant((2012, 4, 28))

            >>> Period((DateUnit.DAY, Instant((2012, 2, 29)), 2)).stop
            Instant((2012, 3, 1))

        """
        unit, start_instant, size = self

        if unit == DateUnit.ETERNITY:
            return Instant.eternity()

        if unit == DateUnit.YEAR:
            date = start_instant.date.add(years=size, days=-1)
            return Instant((date.year, date.month, date.day))

        if unit == DateUnit.MONTH:
            date = start_instant.date.add(months=size, days=-1)
            return Instant((date.year, date.month, date.day))

        if unit == DateUnit.WEEK:
            date = start_instant.date.add(weeks=size, days=-1)
            return Instant((date.year, date.month, date.day))

        if unit in (DateUnit.DAY, DateUnit.WEEKDAY):
            date = start_instant.date.add(days=size - 1)
            return Instant((date.year, date.month, date.day))

        raise ValueError

    @property
    def is_eternal(self) -> bool:
        return self == self.eternity()

    # Reference periods

    @property
    def last_week(self) -> t.Period:
        return self.first_week.offset(-1)

    @property
    def last_fortnight(self) -> t.Period:
        start: t.Instant = self.first_week.start
        return self.__class__((DateUnit.WEEK, start, 1)).offset(-2)

    @property
    def last_2_weeks(self) -> t.Period:
        start: t.Instant = self.first_week.start
        return self.__class__((DateUnit.WEEK, start, 2)).offset(-2)

    @property
    def last_26_weeks(self) -> t.Period:
        start: t.Instant = self.first_week.start
        return self.__class__((DateUnit.WEEK, start, 26)).offset(-26)

    @property
    def last_52_weeks(self) -> t.Period:
        start: t.Instant = self.first_week.start
        return self.__class__((DateUnit.WEEK, start, 52)).offset(-52)

    @property
    def last_month(self) -> t.Period:
        return self.first_month.offset(-1)

    @property
    def last_3_months(self) -> t.Period:
        start: t.Instant = self.first_month.start
        return self.__class__((DateUnit.MONTH, start, 3)).offset(-3)

    @property
    def last_year(self) -> t.Period:
        start: None | t.Instant = self.start.offset("first-of", DateUnit.YEAR)
        if start is None:
            raise NotImplementedError
        return self.__class__((DateUnit.YEAR, start, 1)).offset(-1)

    @property
    def n_2(self) -> t.Period:
        start: None | t.Instant = self.start.offset("first-of", DateUnit.YEAR)
        if start is None:
            raise NotImplementedError
        return self.__class__((DateUnit.YEAR, start, 1)).offset(-2)

    @property
    def this_year(self) -> t.Period:
        start: None | t.Instant = self.start.offset("first-of", DateUnit.YEAR)
        if start is None:
            raise NotImplementedError
        return self.__class__((DateUnit.YEAR, start, 1))

    @property
    def first_month(self) -> t.Period:
        start: None | t.Instant = self.start.offset("first-of", DateUnit.MONTH)
        if start is None:
            raise NotImplementedError
        return self.__class__((DateUnit.MONTH, start, 1))

    @property
    def first_day(self) -> t.Period:
        return self.__class__((DateUnit.DAY, self.start, 1))

    @property
    def first_week(self) -> t.Period:
        start: None | t.Instant = self.start.offset("first-of", DateUnit.WEEK)
        if start is None:
            raise NotImplementedError
        return self.__class__((DateUnit.WEEK, start, 1))

    @property
    def first_weekday(self) -> t.Period:
        return self.__class__((DateUnit.WEEKDAY, self.start, 1))

    @classmethod
    def eternity(cls) -> t.Period:
        """Return an eternity period."""
        return cls((DateUnit.ETERNITY, Instant.eternity(), -1))


__all__ = ["Period"]
