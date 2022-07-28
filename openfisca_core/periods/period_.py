from __future__ import annotations

import calendar

from . import config, helpers
from .instant_ import Instant


class Period(tuple):
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
        >>> instant = Instant((2021, 9, 1))
        >>> period = Period(("year", instant, 3))

        >>> repr(Period)
        "<class 'openfisca_core.periods.period_.Period'>"

        >>> repr(period)
        "Period(('year', Instant((2021, 9, 1)), 3))"

        >>> str(period)
        'year:2021-09:3'

        >>> dict([period, instant])
        Traceback (most recent call last):
        ValueError: dictionary update sequence element #0 has length 3; 2 is required

        >>> list(period)
        ['year', Instant((2021, 9, 1)), 3]

        >>> period[0]
        'year'

        >>> period[0] in period
        True

        >>> len(period)
        3

        >>> period == Period(("year", instant, 3))
        True

        >>> period != Period(("year", instant, 3))
        False

        >>> period > Period(("year", instant, 3))
        False

        >>> period < Period(("year", instant, 3))
        False

        >>> period >= Period(("year", instant, 3))
        True

        >>> period <= Period(("year", instant, 3))
        True

        >>> period.date
        Traceback (most recent call last):
        AssertionError: "date" is undefined for a period of size > 1

        >>> Period(("year", instant, 1)).date
        datetime.date(2021, 9, 1)

        >>> period.days
        1096

        >>> period.size
        3

        >>> period.size_in_months
        36

        >>> period.size_in_days
        1096

        >>> period.start
        Instant((2021, 9, 1))

        >>> period.stop
        Instant((2024, 8, 31))

        >>> period.unit
        'year'

        >>> period.last_3_months
        Period(('month', Instant((2021, 6, 1)), 3))

        >>> period.last_month
        Period(('month', Instant((2021, 8, 1)), 1))

        >>> period.last_year
        Period(('year', Instant((2020, 1, 1)), 1))

        >>> period.n_2
        Period(('year', Instant((2019, 1, 1)), 1))

        >>> period.this_year
        Period(('year', Instant((2021, 1, 1)), 1))

        >>> period.first_month
        Period(('month', Instant((2021, 9, 1)), 1))

        >>> period.first_day
        Period(('day', Instant((2021, 9, 1)), 1))


    Since a period is a triple it can be used as a dictionary key.

    """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({super().__repr__()})"

    def __str__(self) -> str:
        """Transform period to a string.

        Examples:
            >>> str(Period(("year", Instant((2021, 1, 1)), 1)))
            '2021'

            >>> str(Period(("year", Instant((2021, 2, 1)), 1)))
            'year:2021-02'

            >>> str(Period(("month", Instant((2021, 2, 1)), 1)))
            '2021-02'

            >>> str(Period(("year", Instant((2021, 1, 1)), 2)))
            'year:2021:2'

            >>> str(Period(("month", Instant((2021, 1, 1)), 2)))
            'month:2021-01:2'

            >>> str(Period(("month", Instant((2021, 1, 1)), 12)))
            '2021'

            >>> str(Period(("year", Instant((2021, 3, 1)), 2)))
            'year:2021-03:2'

            >>> str(Period(("month", Instant((2021, 3, 1)), 2)))
            'month:2021-03:2'

            >>> str(Period(("month", Instant((2021, 3, 1)), 12)))
            'year:2021-03'

        """

        unit, start_instant, size = self
        if unit == config.ETERNITY:
            return "ETERNITY"
        year, month, day = start_instant

        # 1 year long period
        if unit == config.MONTH and size == 12 or unit == config.YEAR and size == 1:
            if month == 1:
                # civil year starting from january
                return str(year)
            else:
                # rolling year
                return "{}:{}-{:02d}".format(config.YEAR, year, month)
        # simple month
        if unit == config.MONTH and size == 1:
            return "{}-{:02d}".format(year, month)
        # several civil years
        if unit == config.YEAR and month == 1:
            return "{}:{}:{}".format(unit, year, size)

        if unit == config.DAY:
            if size == 1:
                return "{}-{:02d}-{:02d}".format(year, month, day)
            else:
                return "{}:{}-{:02d}-{:02d}:{}".format(unit, year, month, day, size)

        # complex period
        return "{}:{}-{:02d}:{}".format(unit, year, month, size)

    @property
    def date(self):
        assert (
            self.size == 1
        ), '"date" is undefined for a period of size > 1: {}'.format(self)
        return self.start.date

    @property
    def days(self) -> int:
        """Count the number of days in period."""

        return (self.stop.date - self.start.date).days + 1

    def intersection(self, start, stop):
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
                    "year",
                    intersection_start,
                    intersection_stop.year - intersection_start.year + 1,
                )
            )
        if (
            intersection_start.day == 1
            and intersection_stop.day
            == calendar.monthrange(intersection_stop.year, intersection_stop.month)[1]
        ):
            return self.__class__(
                (
                    "month",
                    intersection_start,
                    (
                        (intersection_stop.year - intersection_start.year) * 12
                        + intersection_stop.month
                        - intersection_start.month
                        + 1
                    ),
                )
            )
        return self.__class__(
            (
                "day",
                intersection_start,
                (intersection_stop.date - intersection_start.date).days + 1,
            )
        )

    def get_subperiods(self, unit):
        """Return the list of all the periods of unit ``unit`` contained in self.

        Examples:
            >>> period = Period(("year", Instant((2021, 1, 1)), 1))
            >>> period.get_subperiods("month")
            [Period(('month', Instant((2021, 1, 1)), 1)), ...2021, 12, 1)), 1))]

            >>> period = Period(("year", Instant((2021, 1, 1)), 2))
            >>> period.get_subperiods("year")
            [Period(('year', Instant((2021, 1, 1)), 1)), ...((2022, 1, 1)), 1))]

        """

        if helpers.unit_weight(self.unit) < helpers.unit_weight(unit):
            raise ValueError("Cannot subdivide {0} into {1}".format(self.unit, unit))

        if unit == config.YEAR:
            return [self.this_year.offset(i, config.YEAR) for i in range(self.size)]

        if unit == config.MONTH:
            return [
                self.first_month.offset(i, config.MONTH)
                for i in range(self.size_in_months)
            ]

        if unit == config.DAY:
            return [
                self.first_day.offset(i, config.DAY) for i in range(self.size_in_days)
            ]

    def offset(self, offset: int, unit: str = None):
        """Increment (or decrement) the given period with offset units.

        Args:
            offset (int): number of units to add (or remove if negative).
            unit (str): unit of the offset (default: self.unit).

        Returns:
            Period: the offset period.

        Examples:
            >>> Period(("day", Instant((2021, 1, 1)), 365)).offset(1)
            Period(('day', Instant((2021, 1, 2)), 365))

            >>> Period(("day", Instant((2021, 1, 1)), 365)).offset(1, "day")
            Period(('day', Instant((2021, 1, 2)), 365))

            >>> Period(("day", Instant((2021, 1, 1)), 365)).offset(1, "month")
            Period(('day', Instant((2021, 2, 1)), 365))

            >>> Period(("day", Instant((2021, 1, 1)), 365)).offset(1, "year")
            Period(('day', Instant((2022, 1, 1)), 365))

            >>> Period(("month", Instant((2021, 1, 1)), 12)).offset(1)
            Period(('month', Instant((2021, 2, 1)), 12))

            >>> Period(("month", Instant((2021, 1, 1)), 12)).offset(1, "day")
            Period(('month', Instant((2021, 1, 2)), 12))

            >>> Period(("month", Instant((2021, 1, 1)), 12)).offset(1, "month")
            Period(('month', Instant((2021, 2, 1)), 12))

            >>> Period(("month", Instant((2021, 1, 1)), 12)).offset(1, "year")
            Period(('month', Instant((2022, 1, 1)), 12))

            >>> Period(("year", Instant((2021, 1, 1)), 1)).offset(1)
            Period(('year', Instant((2022, 1, 1)), 1))

            >>> Period(("year", Instant((2021, 1, 1)), 1)).offset(1, "day")
            Period(('year', Instant((2021, 1, 2)), 1))

            >>> Period(("year", Instant((2021, 1, 1)), 1)).offset(1, "month")
            Period(('year', Instant((2021, 2, 1)), 1))

            >>> Period(("year", Instant((2021, 1, 1)), 1)).offset(1, "year")
            Period(('year', Instant((2022, 1, 1)), 1))

            >>> Period(("day", Instant((2011, 2, 28)), 1)).offset(1)
            Period(('day', Instant((2011, 3, 1)), 1))

            >>> Period(("month", Instant((2011, 2, 28)), 1)).offset(1)
            Period(('month', Instant((2011, 3, 28)), 1))

            >>> Period(("year", Instant((2011, 2, 28)), 1)).offset(1)
            Period(('year', Instant((2012, 2, 28)), 1))

            >>> Period(("day", Instant((2011, 3, 1)), 1)).offset(-1)
            Period(('day', Instant((2011, 2, 28)), 1))

            >>> Period(("month", Instant((2011, 3, 1)), 1)).offset(-1)
            Period(('month', Instant((2011, 2, 1)), 1))

            >>> Period(("year", Instant((2011, 3, 1)), 1)).offset(-1)
            Period(('year', Instant((2010, 3, 1)), 1))

            >>> Period(("day", Instant((2014, 1, 30)), 1)).offset(3)
            Period(('day', Instant((2014, 2, 2)), 1))

            >>> Period(("month", Instant((2014, 1, 30)), 1)).offset(3)
            Period(('month', Instant((2014, 4, 30)), 1))

            >>> Period(("year", Instant((2014, 1, 30)), 1)).offset(3)
            Period(('year', Instant((2017, 1, 30)), 1))

            >>> Period(("day", Instant((2021, 1, 1)), 365)).offset(-3)
            Period(('day', Instant((2020, 12, 29)), 365))

            >>> Period(("month", Instant((2021, 1, 1)), 12)).offset(-3)
            Period(('month', Instant((2020, 10, 1)), 12))

            >>> Period(("year", Instant((2014, 1, 1)), 1)).offset(-3)
            Period(('year', Instant((2011, 1, 1)), 1))

            >>> Period(("day", Instant((2014, 2, 3)), 1)).offset("first-of", "month")
            Period(('day', Instant((2014, 2, 1)), 1))

            >>> Period(("day", Instant((2014, 2, 3)), 1)).offset("first-of", "year")
            Period(('day', Instant((2014, 1, 1)), 1))

            >>> Period(("day", Instant((2014, 2, 3)), 4)).offset("first-of", "month")
            Period(('day', Instant((2014, 2, 1)), 4))

            >>> Period(("day", Instant((2014, 2, 3)), 4)).offset("first-of", "year")
            Period(('day', Instant((2014, 1, 1)), 4))

            >>> Period(("month", Instant((2014, 2, 3)), 1)).offset("first-of")
            Period(('month', Instant((2014, 2, 1)), 1))

            >>> Period(("month", Instant((2014, 2, 3)), 1)).offset("first-of", "month")
            Period(('month', Instant((2014, 2, 1)), 1))

            >>> Period(("month", Instant((2014, 2, 3)), 1)).offset("first-of", "year")
            Period(('month', Instant((2014, 1, 1)), 1))

            >>> Period(("month", Instant((2014, 2, 3)), 4)).offset("first-of")
            Period(('month', Instant((2014, 2, 1)), 4))

            >>> Period(("month", Instant((2014, 2, 3)), 4)).offset("first-of", "month")
            Period(('month', Instant((2014, 2, 1)), 4))

            >>> Period(("month", Instant((2014, 2, 3)), 4)).offset("first-of", "year")
            Period(('month', Instant((2014, 1, 1)), 4))

            >>> Period(("year", Instant((2014, 1, 30)), 1)).offset("first-of")
            Period(('year', Instant((2014, 1, 1)), 1))

            >>> Period(("year", Instant((2014, 1, 30)), 1)).offset("first-of", "month")
            Period(('year', Instant((2014, 1, 1)), 1))

            >>> Period(("year", Instant((2014, 1, 30)), 1)).offset("first-of", "year")
            Period(('year', Instant((2014, 1, 1)), 1))

            >>> Period(("year", Instant((2014, 2, 3)), 1)).offset("first-of")
            Period(('year', Instant((2014, 1, 1)), 1))

            >>> Period(("year", Instant((2014, 2, 3)), 1)).offset("first-of", "month")
            Period(('year', Instant((2014, 2, 1)), 1))

            >>> Period(("year", Instant((2014, 2, 3)), 1)).offset("first-of", "year")
            Period(('year', Instant((2014, 1, 1)), 1))

            >>> Period(("day", Instant((2014, 2, 3)), 1)).offset("last-of", "month")
            Period(('day', Instant((2014, 2, 28)), 1))

            >>> Period(("day", Instant((2014, 2, 3)), 1)).offset("last-of", "year")
            Period(('day', Instant((2014, 12, 31)), 1))

            >>> Period(("day", Instant((2014, 2, 3)), 4)).offset("last-of", "month")
            Period(('day', Instant((2014, 2, 28)), 4))

            >>> Period(("day", Instant((2014, 2, 3)), 4)).offset("last-of", "year")
            Period(('day', Instant((2014, 12, 31)), 4))

            >>> Period(("month", Instant((2014, 2, 3)), 1)).offset("last-of")
            Period(('month', Instant((2014, 2, 28)), 1))

            >>> Period(("month", Instant((2014, 2, 3)), 1)).offset("last-of", "month")
            Period(('month', Instant((2014, 2, 28)), 1))

            >>> Period(("month", Instant((2014, 2, 3)), 1)).offset("last-of", "year")
            Period(('month', Instant((2014, 12, 31)), 1))

            >>> Period(("month", Instant((2014, 2, 3)), 4)).offset("last-of")
            Period(('month', Instant((2014, 2, 28)), 4))

            >>> Period(("month", Instant((2014, 2, 3)), 4)).offset("last-of", "month")
            Period(('month', Instant((2014, 2, 28)), 4))

            >>> Period(("month", Instant((2014, 2, 3)), 4)).offset("last-of", "year")
            Period(('month', Instant((2014, 12, 31)), 4))

            >>> Period(("year", Instant((2014, 2, 3)), 1)).offset("last-of")
            Period(('year', Instant((2014, 12, 31)), 1))

            >>> Period(("year", Instant((2014, 1, 1)), 1)).offset("last-of", "month")
            Period(('year', Instant((2014, 1, 31)), 1))

            >>> Period(("year", Instant((2014, 2, 3)), 1)).offset("last-of", "year")
            Period(('year', Instant((2014, 12, 31)), 1))

            >>> Period(("year", Instant((2014, 2, 3)), 1)).offset("last-of")
            Period(('year', Instant((2014, 12, 31)), 1))

            >>> Period(("year", Instant((2014, 2, 3)), 1)).offset("last-of", "month")
            Period(('year', Instant((2014, 2, 28)), 1))

            >>> Period(("year", Instant((2014, 2, 3)), 1)).offset("last-of", "year")
            Period(('year', Instant((2014, 12, 31)), 1))

        """

        return self.__class__(
            (
                self[0],
                self[1].offset(offset, self[0] if unit is None else unit),
                self[2],
            )
        )

    def contains(self, other: Period) -> bool:
        """Return ``True`` if the period contains ``other``.

        For instance, ``period(2015)`` contains ``period(2015-01)``.

        """

        return self.start <= other.start and self.stop >= other.stop

    @property
    def size(self) -> int:
        """Return the size of the period."""

        return self[2]

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

        raise ValueError(f"Can't calculate number of months in a {self.unit}.")

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
            last_day = self.start.offset(self.size, self.unit).offset(-1, DateUnit.DAY)
            return (last_day.date - self.start.date).days + 1

        if self.unit == DateUnit.WEEK:
            return self.size * 7

        if self.unit in (DateUnit.DAY, DateUnit.WEEKDAY):
            return self.size

        raise ValueError(f"Can't calculate number of days in a {self.unit}.")

    @property
    def start(self) -> Instant:
        """Return the first day of the period as an Instant instance."""

        return self[1]

    @property
    def stop(self) -> Instant:
        """Return the last day of the period as an Instant instance.

        Examples:
            >>> Period(("year", Instant((2022, 1, 1)), 1)).stop
            Instant((2022, 12, 31))

            >>> Period(("month", Instant((2022, 1, 1)), 12)).stop
            Instant((2022, 12, 31))

            >>> Period(("day", Instant((2022, 1, 1)), 365)).stop
            Instant((2022, 12, 31))

            >>> Period(("year", Instant((2012, 2, 29)), 1)).stop
            Instant((2013, 2, 28))

            >>> Period(("month", Instant((2012, 2, 29)), 1)).stop
            Instant((2012, 3, 28))

            >>> Period(("day", Instant((2012, 2, 29)), 1)).stop
            Instant((2012, 2, 29))

            >>> Period(("year", Instant((2012, 2, 29)), 2)).stop
            Instant((2014, 2, 28))

            >>> Period(("month", Instant((2012, 2, 29)), 2)).stop
            Instant((2012, 4, 28))

            >>> Period(("day", Instant((2012, 2, 29)), 2)).stop
            Instant((2012, 3, 1))

        """

        unit, start_instant, size = self
        year, month, day = start_instant
        if unit == config.ETERNITY:
            return Instant((float("inf"), float("inf"), float("inf")))
        if unit == "day":
            if size > 1:
                day += size - 1
                month_last_day = calendar.monthrange(year, month)[1]
                while day > month_last_day:
                    month += 1
                    if month == 13:
                        year += 1
                        month = 1
                    day -= month_last_day
                    month_last_day = calendar.monthrange(year, month)[1]
        else:
            if unit == "month":
                month += size
                while month > 12:
                    year += 1
                    month -= 12
            else:
                assert unit == "year", "Invalid unit: {} of type {}".format(
                    unit, type(unit)
                )
                year += size
            day -= 1
            if day < 1:
                month -= 1
                if month == 0:
                    year -= 1
                    month = 12
                day += calendar.monthrange(year, month)[1]
            else:
                month_last_day = calendar.monthrange(year, month)[1]
                if day > month_last_day:
                    month += 1
                    if month == 13:
                        year += 1
                        month = 1
                    day -= month_last_day
        return Instant((year, month, day))

    @property
    def unit(self) -> str:
        return self[0]

    # Reference periods

    @property
    def last_month(self) -> Period:
        return self.first_month.offset(-1)

    @property
    def last_3_months(self) -> Period:
        start: Instant = self.first_month.start
        return self.__class__((config.MONTH, start, 3)).offset(-3)

    @property
    def last_year(self) -> Period:
        start: Instant = self.start.offset("first-of", config.YEAR)
        return self.__class__((config.YEAR, start, 1)).offset(-1)

    @property
    def n_2(self) -> Period:
        start: Instant = self.start.offset("first-of", config.YEAR)
        return self.__class__((config.YEAR, start, 1)).offset(-2)

    @property
    def this_year(self) -> Period:
        start: Instant = self.start.offset("first-of", config.YEAR)
        return self.__class__((config.YEAR, start, 1))

    @property
    def first_month(self) -> Period:
        start: Instant = self.start.offset("first-of", config.MONTH)
        return self.__class__((config.MONTH, start, 1))

    @property
    def first_day(self) -> Period:
        return self.__class__((config.DAY, self.start, 1))
