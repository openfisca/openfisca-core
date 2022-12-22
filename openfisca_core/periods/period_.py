from __future__ import annotations

from typing import NamedTuple, Sequence

import datetime

from ._dates import DateUnit
from ._errors import DateUnitValueError
from .typing import Offsetable

DAY, MONTH, YEAR, ETERNITY = tuple(DateUnit)

Instant = Offsetable[int, int, int]


class Period(NamedTuple):
    """Toolbox to handle date intervals.

    Examples:
        >>> from openfisca_core.periods import Instant

        >>> start = Instant(2021, 9, 1)
        >>> period = Period(YEAR, start, 3)

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

        >>> period == Period(YEAR, start, 3)
        True

        >>> period > Period(YEAR, start, 3)
        False

        >>> unit, (year, month, day), size = period

    Since a period is a triple it can be used as a dictionary key.

    """

    #: Either ``year``, ``month``, ``day`` or ``eternity``.
    unit: DateUnit

    #: The "instant" the Period starts at.
    start: Offsetable[int, int, int]

    #: The amount of ``unit``, starting at ``start``, at least ``1``.
    size: int

    def __str__(self) -> str:
        """Transform period to a string.

        Returns:
            A string representation of the period.

        Examples:
            >>> from openfisca_core.periods import Instant

            >>> jan = Instant(2021, 1, 1)
            >>> feb = jan.offset(1, MONTH)

            >>> str(Period(YEAR, jan, 1))
            '2021'

            >>> str(Period(YEAR, feb, 1))
            'year:2021-02'

            >>> str(Period(MONTH, feb, 1))
            '2021-02'

            >>> str(Period(YEAR, jan, 2))
            'year:2021:2'

            >>> str(Period(MONTH, jan, 2))
            'month:2021-01:2'

            >>> str(Period(MONTH, jan, 12))
            '2021'

        """

        year: int
        month: int
        day: int

        unit, (year, month, day), size = self

        if unit == ETERNITY:
            return str(unit.name)

        # 1 year long period
        if unit == MONTH and size == 12 or unit == YEAR and size == 1:
            if month == 1:
                # civil year starting from january
                return str(year)

            else:
                # rolling year
                return f"{str(YEAR)}:{year}-{month:02d}"

        # simple month
        if unit == MONTH and size == 1:
            return f"{year}-{month:02d}"

        # several civil years
        if unit == YEAR and month == 1:
            return f"{str(unit)}:{year}:{size}"

        if unit == DAY:
            if size == 1:
                return f"{year}-{month:02d}-{day:02d}"

            else:
                return f"{str(unit)}:{year}-{month:02d}-{day:02d}:{size}"

        # complex period
        return f"{str(unit)}:{year}-{month:02d}:{size}"

    def __contains__(self, other: object) -> bool:
        """Checks if a ``period`` contains another one.

        Args:
            other: The other ``Period``.

        Returns:
            True if ``other`` is contained, otherwise False.

        Example:
            >>> from openfisca_core.periods import Instant

            >>> start = Instant(2021, 1, 1)
            >>> period = Period(YEAR, start, 1)
            >>> sub_period = Period(MONTH, start, 3)

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

            >>> Period(YEAR, start, 2).stop
            Instant(year=2014, month=2, day=27)

            >>> Period(MONTH, start, 36).stop
            Instant(year=2015, month=2, day=27)

            >>> Period(DAY, start, 1096).stop
            Instant(year=2015, month=2, day=28)

        """

        unit, start, size = self

        if unit == ETERNITY:
            return type(self.start)((1, 1, 1))

        return start.offset(size, unit).offset(-1, DAY)

    def date(self) -> datetime.date:
        """The date representation of the ``period``'s' start date.

        Returns:
            A datetime.date.

        Raises:
            ValueError: If the period's size is greater than 1.

        Examples:
            >>> from openfisca_core.periods import Instant

            >>> start = Instant(2021, 10, 1)

            >>> period = Period(YEAR, start, 1)
            >>> period.date()
            Date(2021, 10, 1)

            >>> period = Period(YEAR, start, 3)
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

            >>> period = Period(YEAR, start, 3)
            >>> period.count(DAY)
            1096

            >>> period = Period(MONTH, start, 3)
            >>> period.count(DAY)
            92

            >>> period = Period(YEAR, start, 3)
            >>> period.count(MONTH)
            36

            >>> period = Period(DAY, start, 3)
            >>> period.count(MONTH)
            Traceback (most recent call last):
            ValueError: Cannot calculate number of months in a day.

            >>> period = Period(YEAR, start, 3)
            >>> period.count(YEAR)
            3

            >>> period = Period(MONTH, start, 3)
            >>> period.count(YEAR)
            Traceback (most recent call last):
            ValueError: Cannot calculate number of years in a month.

        .. versionadded:: 39.0.0

        """

        if unit == self.unit:
            return self.size

        if unit == DAY and self.unit in {MONTH, YEAR}:
            delta: int = (self.stop.date() - self.start.date()).days
            return delta + 1

        if unit == MONTH and self.unit == YEAR:
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

            >>> period = Period(YEAR, start, 3)

            >>> period.first(DAY)
            Period(unit=day, start=Instant(year=2023, month=1, day=1), size=1)

            >>> period.first(MONTH)
            Period(unit=month, start=Instant(year=2023, month=1, day=1), size=1)

            >>> period.first(YEAR)
            Period(unit=year, start=Instant(year=2023, month=1, day=1), size=1)

        .. versionadded:: 39.0.0

        """

        return type(self)(unit, self.start.offset("first-of", unit), 1)

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

            >>> period = Period(YEAR, start, 3)

            >>> period.come(DAY)
            Period(unit=day, start=Instant(year=2023, month=1, day=2), size=1)

            >>> period.come(DAY, 7)
            Period(unit=day, start=Instant(year=2023, month=1, day=8), size=1)

            >>> period.come(MONTH)
            Period(unit=month, start=Instant(year=2023, month=2, day=1), size=1)

            >>> period.come(MONTH, 3)
            Period(unit=month, start=Instant(year=2023, month=4, day=1), size=1)

            >>> period.come(YEAR)
            Period(unit=year, start=Instant(year=2024, month=1, day=1), size=1)

            >>> period.come(YEAR, 1)
            Period(unit=year, start=Instant(year=2024, month=1, day=1), size=1)

        .. versionadded:: 39.0.0

        """

        return type(self)(unit, self.first(unit).start, 1).offset(size)

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

            >>> period = Period(YEAR, start, 3)

            >>> period.ago(DAY)
            Period(unit=day, start=Instant(year=2020, month=3, day=30), size=1)

            >>> period.ago(DAY, 7)
            Period(unit=day, start=Instant(year=2020, month=3, day=24), size=1)

            >>> period.ago(MONTH)
            Period(unit=month, start=Instant(year=2020, month=2, day=29), size=1)

            >>> period.ago(MONTH, 3)
            Period(unit=month, start=Instant(year=2019, month=12, day=31), size=1)

            >>> period.ago(YEAR)
            Period(unit=year, start=Instant(year=2019, month=3, day=31), size=1)

            >>> period.ago(YEAR, 1)
            Period(unit=year, start=Instant(year=2019, month=3, day=31), size=1)

        .. versionadded:: 39.0.0

        """

        return type(self)(unit, self.start, 1).offset(-size)

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

            >>> period = Period(YEAR, start, 3)

            >>> period.until(DAY)
            Period(unit=day, start=Instant(year=2023, month=1, day=1), size=1)

            >>> period.until(DAY, 7)
            Period(unit=day, start=Instant(year=2023, month=1, day=1), size=7)

            >>> period.until(MONTH)
            Period(unit=month, start=Instant(year=2023, month=1, day=1), size=1)

            >>> period.until(MONTH, 3)
            Period(unit=month, start=Instant(year=2023, month=1, day=1), size=3)

            >>> period.until(YEAR)
            Period(unit=year, start=Instant(year=2023, month=1, day=1), size=1)

            >>> period.until(YEAR, 1)
            Period(unit=year, start=Instant(year=2023, month=1, day=1), size=1)

        .. versionadded:: 39.0.0

        """

        return type(self)(unit, self.first(unit).start, size)

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

            >>> period = Period(YEAR, start, 3)

            >>> period.last(DAY)
            Period(unit=day, start=Instant(year=2022, month=12, day=31), size=1)

            >>> period.last(DAY, 7)
            Period(unit=day, start=Instant(year=2022, month=12, day=25), size=7)

            >>> period.last(MONTH)
            Period(unit=month, start=Instant(year=2022, month=12, day=1), size=1)

            >>> period.last(MONTH, 3)
            Period(unit=month, start=Instant(year=2022, month=10, day=1), size=3)

            >>> period.last(YEAR)
            Period(unit=year, start=Instant(year=2022, month=1, day=1), size=1)

            >>> period.last(YEAR, 1)
            Period(unit=year, start=Instant(year=2022, month=1, day=1), size=1)

        .. versionadded:: 39.0.0

        """

        return type(self)(unit, self.ago(unit, size).start, size)

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

            >>> Period(DAY, start, 1).offset("first-of", MONTH)
            Period(unit=day, start=Instant(year=2014, month=2, day=1), size=1)

            >>> Period(MONTH, start, 4).offset("last-of", MONTH)
            Period(unit=month, start=Instant(year=2014, month=2, day=28), size=4)

            >>> start = Instant(2021, 1, 1)

            >>> Period(DAY, start, 365).offset(-3)
            Period(unit=day, start=Instant(year=2020, month=12, day=29), size=365)

            >>> Period(DAY, start, 365).offset(1, YEAR)
            Period(unit=day, start=Instant(year=2022, month=1, day=1), size=365)

        """

        if unit is None:
            unit = self.unit

        start = self.start.offset(offset, unit)

        return type(self)(self.unit, start, self.size)

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

            >>> period = Period(YEAR, start, 1)
            >>> period.subperiods(MONTH)
            [Period(unit=month, start=Instant(year=2021, month=1, day=1), size=1), ...]

            >>> period = Period(YEAR, start, 2)
            >>> period.subperiods(YEAR)
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
