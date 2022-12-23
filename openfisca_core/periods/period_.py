from __future__ import annotations

from typing import NamedTuple, Sequence

import datetime

from ._dates import DateUnit
from ._errors import DateUnitValueError
from .typing import Instant

day, month, year, eternity = tuple(DateUnit)


class Period(NamedTuple):
    """Toolbox to handle date intervals.

    Examples:
        >>> from openfisca_core.periods import Instant

        >>> start = Instant(2021, 9, 1)
        >>> period = Period(year, start, 3)

        ``Periods`` are represented as a ``tuple`` containing the ``unit``,
        an ``Instant`` and the ``size``:

        >>> repr(period)
        'Period(unit=year, start=Instant(year=2021, month=9, day=1), size=3)'

        Their user-friendly representation is as a date in the
        ISO format, prefixed with the ``unit`` and suffixed with its ``size``:

        >>> str(period)
        'year:2021-09:3'

        However, you won't be able to use them as hashmaps keys. Because they
        contain a nested data structure, they're not hashable:

        >>> {period: (2021, 9, 13)}
        {Period(unit=year, start=Instant(year=2021, month=9, day=1), size=3):...}

        All the rest of the ``tuple`` protocols are inherited as well:

        >>> period.unit
        year

        >>> period.unit in period
        True

        >>> len(period)
        3

        >>> period == Period(year, start, 3)
        True

        >>> period > Period(year, start, 3)
        False

    Since a period is a triple it can be used as a dictionary key.

    """

    #: Either ``year``, ``month``, ``day`` or ``eternity``.
    unit: DateUnit

    #: The "instant" the Period starts at.
    start: Instant

    #: The amount of ``unit``, starting at ``start``, at least ``1``.
    size: int

    def __str__(self) -> str:
        """Transform period to a string.

        Returns:
            A string representation of the period.

        Examples:
            >>> from openfisca_core.periods import Instant

            >>> jan = Instant(2021, 1, 1)
            >>> feb = jan.offset(1, month)

            >>> str(Period(year, jan, 1))
            '2021'

            >>> str(Period(year, feb, 1))
            'year:2021-02:1'

            >>> str(Period(month, feb, 1))
            '2021-02'

            >>> str(Period(year, jan, 2))
            'year:2021:2'

            >>> str(Period(month, jan, 2))
            'month:2021-01:2'

            >>> str(Period(month, jan, 12))
            'month:2021-01:12'

        """

        if self.unit == eternity:
            return str(self.unit.name)

        string = f"{self.start.year:04d}"

        if self.unit == year and self.start.month > 1:
            string = f"{string}-{self.start.month:02d}"

        if self.unit < year:
            string = f"{string}-{self.start.month:02d}"

        if self.unit < month:
            string = f"{string}-{self.start.day:02d}"

        if self.unit == year and self.start.month > 1:
            return f"{str(self.unit)}:{string}:{self.size}"

        if self.size > 1:
            return f"{str(self.unit)}:{string}:{self.size}"

        return string

    def __contains__(self, other: object) -> bool:
        """Checks if a ``period`` contains another one.

        Args:
            other: The other ``Period``.

        Returns:
            True if ``other`` is contained, otherwise False.

        Example:
            >>> from openfisca_core.periods import Instant

            >>> start = Instant(2021, 1, 1)
            >>> period = Period(year, start, 1)
            >>> sub_period = Period(month, start, 3)

            >>> sub_period in period
            True

        """

        if isinstance(other, Period):
            return self.start <= other.start and self.stop >= other.stop

        return super().__contains__(other)

    @property
    def stop(self) -> Instant:
        """Last day of the ``Period`` as an ``Instant``.

        Returns:
            An Instant.

        Examples:
            >>> from openfisca_core.periods import Instant

            >>> start = Instant(2012, 2, 29)

            >>> Period(year, start, 2).stop
            Instant(year=2014, month=2, day=27)

            >>> Period(month, start, 36).stop
            Instant(year=2015, month=2, day=27)

            >>> Period(day, start, 1096).stop
            Instant(year=2015, month=2, day=28)

        """

        if self.unit == eternity:
            return type(self.start)(1, 1, 1)

        return self.start.offset(self.size, self.unit).offset(-1, day)

    def date(self) -> datetime.date:
        """The date representation of the ``period``'s' start date.

        Returns:
            A datetime.date.

        Raises:
            ValueError: If the period's size is greater than 1.

        Examples:
            >>> from openfisca_core.periods import Instant

            >>> start = Instant(2021, 10, 1)

            >>> period = Period(year, start, 1)
            >>> period.date()
            Date(2021, 10, 1)

            >>> period = Period(year, start, 3)
            >>> period.date()
            Traceback (most recent call last):
            ValueError: 'date' undefined for period size > 1: year:2021-10:3.

        .. versionchanged:: 39.0.0:
            Made it a normal method instead of a property.

        """

        if self.size > 1:
            raise ValueError(f"'date' undefined for period size > 1: {self}.")

        return self.start.date()

    def count(self, unit: DateUnit) -> int:
        """The ``size`` of the ``Period`` in the given unit.

        Args:
            unit: The unit to convert to.

        Returns:
            An int.

        Raises:
            ValueError: If the period's unit is not a day, a month or a year.

        Examples:
            >>> from openfisca_core.periods import Instant

            >>> start = Instant(2021, 10, 1)

            >>> period = Period(year, start, 3)
            >>> period.count(day)
            1096

            >>> period = Period(month, start, 3)
            >>> period.count(day)
            92

            >>> period = Period(year, start, 3)
            >>> period.count(month)
            36

            >>> period = Period(day, start, 3)
            >>> period.count(month)
            Traceback (most recent call last):
            ValueError: Cannot calculate number of months in a day.

            >>> period = Period(year, start, 3)
            >>> period.count(year)
            3

            >>> period = Period(month, start, 3)
            >>> period.count(year)
            Traceback (most recent call last):
            ValueError: Cannot calculate number of years in a month.

        .. versionadded:: 39.0.0

        """

        if unit == self.unit:
            return self.size

        if unit == day and self.unit in {month, year}:
            delta: int = (self.stop.date() - self.start.date()).days
            return delta + 1

        if unit == month and self.unit == year:
            return self.size * 12

        raise ValueError(
            f"Cannot calculate number of {unit.plural} in a "
            f"{str(self.unit)}."
            )

    def first(self, unit: DateUnit) -> Period:
        """A new month ``Period`` starting at the first of ``unit``.

        Args:
            unit: The unit of the requested Period.

        Returns:
            A Period.

        Examples:
            >>> from openfisca_core.periods import Instant

            >>> start = Instant(2023, 1, 1)

            >>> period = Period(year, start, 3)

            >>> period.first(day)
            Period(unit=day, start=Instant(year=2023, month=1, day=1), size=1)

            >>> period.first(month)
            Period(unit=month, start=Instant(year=2023, month=1, day=1), size=1)

            >>> period.first(year)
            Period(unit=year, start=Instant(year=2023, month=1, day=1), size=1)

        .. versionadded:: 39.0.0

        """

        start: Instant = self.start.offset("first-of", unit)

        return Period(unit, start, 1)

    def come(self, unit: DateUnit, size: int = 1) -> Period:
        """The next ``unit``s ``size`` from ``Period.start``.

        Args:
            unit: The unit of the requested Period.
            size: The number of units ago.

        Returns:
            A Period.

        Examples:
            >>> from openfisca_core.periods import Instant

            >>> start = Instant(2023, 1, 1)

            >>> period = Period(year, start, 3)

            >>> period.come(day)
            Period(unit=day, start=Instant(year=2023, month=1, day=2), size=1)

            >>> period.come(day, 7)
            Period(unit=day, start=Instant(year=2023, month=1, day=8), size=1)

            >>> period.come(month)
            Period(unit=month, start=Instant(year=2023, month=2, day=1), size=1)

            >>> period.come(month, 3)
            Period(unit=month, start=Instant(year=2023, month=4, day=1), size=1)

            >>> period.come(year)
            Period(unit=year, start=Instant(year=2024, month=1, day=1), size=1)

            >>> period.come(year, 1)
            Period(unit=year, start=Instant(year=2024, month=1, day=1), size=1)

        .. versionadded:: 39.0.0

        """

        start: Instant = self.first(unit).start

        return Period(unit, start, 1).offset(size)

    def ago(self, unit: DateUnit, size: int = 1) -> Period:
        """``size`` ``unit``s ago from ``Period.start``.

        Args:
            unit: The unit of the requested Period.
            size: The number of units ago.

        Returns:
            A Period.

        Examples:
            >>> from openfisca_core.periods import Instant

            >>> start = Instant(2020, 3, 31)

            >>> period = Period(year, start, 3)

            >>> period.ago(day)
            Period(unit=day, start=Instant(year=2020, month=3, day=30), size=1)

            >>> period.ago(day, 7)
            Period(unit=day, start=Instant(year=2020, month=3, day=24), size=1)

            >>> period.ago(month)
            Period(unit=month, start=Instant(year=2020, month=2, day=29), size=1)

            >>> period.ago(month, 3)
            Period(unit=month, start=Instant(year=2019, month=12, day=31), size=1)

            >>> period.ago(year)
            Period(unit=year, start=Instant(year=2019, month=3, day=31), size=1)

            >>> period.ago(year, 1)
            Period(unit=year, start=Instant(year=2019, month=3, day=31), size=1)

        .. versionadded:: 39.0.0

        """

        start: Instant = self.start

        return Period(unit, start, 1).offset(-size)

    def until(self, unit: DateUnit, size: int = 1) -> Period:
        """Next ``unit`` ``size``s from ``Period.start``.

        Args:
            unit: The unit of the requested Period.
            size: The number of units to include in the Period.

        Returns:
            A Period.

        Examples:
            >>> from openfisca_core.periods import Instant

            >>> start = Instant(2023, 1, 1)

            >>> period = Period(year, start, 3)

            >>> period.until(day)
            Period(unit=day, start=Instant(year=2023, month=1, day=1), size=1)

            >>> period.until(day, 7)
            Period(unit=day, start=Instant(year=2023, month=1, day=1), size=7)

            >>> period.until(month)
            Period(unit=month, start=Instant(year=2023, month=1, day=1), size=1)

            >>> period.until(month, 3)
            Period(unit=month, start=Instant(year=2023, month=1, day=1), size=3)

            >>> period.until(year)
            Period(unit=year, start=Instant(year=2023, month=1, day=1), size=1)

            >>> period.until(year, 1)
            Period(unit=year, start=Instant(year=2023, month=1, day=1), size=1)

        .. versionadded:: 39.0.0

        """

        start: Instant = self.first(unit).start

        return Period(unit, start, size)

    def last(self, unit: DateUnit, size: int = 1) -> Period:
        """Last ``size`` ``unit``s from ``Period.start``.

        Args:
            unit: The unit of the requested Period.
            size: The number of units to include in the Period.

        Returns:
            A Period.

        Examples:
            >>> from openfisca_core.periods import Instant

            >>> start = Instant(2023, 1, 1)

            >>> period = Period(year, start, 3)

            >>> period.last(day)
            Period(unit=day, start=Instant(year=2022, month=12, day=31), size=1)

            >>> period.last(day, 7)
            Period(unit=day, start=Instant(year=2022, month=12, day=25), size=7)

            >>> period.last(month)
            Period(unit=month, start=Instant(year=2022, month=12, day=1), size=1)

            >>> period.last(month, 3)
            Period(unit=month, start=Instant(year=2022, month=10, day=1), size=3)

            >>> period.last(year)
            Period(unit=year, start=Instant(year=2022, month=1, day=1), size=1)

            >>> period.last(year, 1)
            Period(unit=year, start=Instant(year=2022, month=1, day=1), size=1)

        .. versionadded:: 39.0.0

        """

        start: Instant = self.ago(unit, size).start

        return Period(unit, start, size)

    def offset(self, offset: str | int, unit: DateUnit | None = None) -> Period:
        """Increment (or decrement) the given period with offset units.

        Args:
            offset: How much of ``unit`` to offset.
            unit: What to offset.

        Returns:
            Period: A new one.

        Examples:
            >>> from openfisca_core.periods import Instant

            >>> start = Instant(2014, 2, 3)

            >>> Period(day, start, 1).offset("first-of", month)
            Period(unit=day, start=Instant(year=2014, month=2, day=1), size=1)

            >>> Period(month, start, 4).offset("last-of", month)
            Period(unit=month, start=Instant(year=2014, month=2, day=28), size=4)

            >>> start = Instant(2021, 1, 1)

            >>> Period(day, start, 365).offset(-3)
            Period(unit=day, start=Instant(year=2020, month=12, day=29), size=365)

            >>> Period(day, start, 365).offset(1, year)
            Period(unit=day, start=Instant(year=2022, month=1, day=1), size=365)

        """

        if unit is None:
            unit = self.unit

        start: Instant = self.start.offset(offset, unit)

        return Period(self.unit, start, self.size)

    def subperiods(self, unit: DateUnit) -> Sequence[Period]:
        """Return the list of all the periods of unit ``unit``.

        Args:
            unit: A string representing period's ``unit``.

        Returns:
            A list of periods.

        Raises:
            DateUnitValueError: If the ``unit`` is not a valid date unit.
            ValueError: If the period's unit is smaller than the given unit.

        Examples:
            >>> from openfisca_core.periods import Instant

            >>> start = Instant(2021, 1, 1)

            >>> period = Period(year, start, 1)
            >>> period.subperiods(month)
            [Period(unit=month, start=Instant(year=2021, month=1, day=1), size=1), ...]

            >>> period = Period(year, start, 2)
            >>> period.subperiods(year)
            [Period(unit=year, start=Instant(year=2021, month=1, day=1), size=1), ...]

        .. versionchanged:: 39.0.0:
            Renamed from ``get_subperiods`` to ``subperiods``.

        """

        if self.unit < unit:
            raise ValueError(f"Cannot subdivide {self.unit} into {unit}")

        if not unit & DateUnit.isoformat:
            raise DateUnitValueError(unit)

        return [
            self.first(unit).offset(offset, unit)
            for offset in range(self.count(unit))
            ]
