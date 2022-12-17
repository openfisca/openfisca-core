from __future__ import annotations

from typing import Callable, Sequence, Tuple

import inflect
import datetime

from ._errors import DateUnitValueError
from ._units import DAY, ETERNITY, MONTH, UNIT_WEIGHTS, YEAR
from .typing import Instant


class Period(Tuple[str, Instant, int]):
    """Toolbox to handle date intervals.

    A ``Period`` is a triple (``unit``, ``start``, ``size``).

    Attributes:
        unit (str):
            Either ``year``, ``month``, ``day`` or ``eternity``.
        start (:obj:`.Instant`):
            The "instant" the :obj:`.Period` starts at.
        size (int):
            The amount of ``unit``, starting at ``start``, at least ``1``.

    Args:
        tuple(str, .Instant, int))):
            The ``unit``, ``start``, and ``size``, accordingly.

    Examples:
        >>> from openfisca_core import periods

        >>> start = periods.Instant((2021, 9, 1))
        >>> period = Period((YEAR, start, 3))

        ``Periods`` are represented as a ``tuple`` containing the ``unit``,
        an ``Instant`` and the ``size``:

        >>> repr(period)
        "Period(('year', Instant((2021, 9, 1)), 3))"

        Their user-friendly representation is as a date in the
        ISO format, prefixed with the ``unit`` and suffixed with its ``size``:

        >>> str(period)
        'year:2021-09:3'

        However, you won't be able to use them as hashmaps keys. Because they
        contain a nested data structure, they're not hashable:

        >>> dict([period, (2021, 9, 13)])
        Traceback (most recent call last):
        ValueError: dictionary update sequence element #0 has length 3...

        All the rest of the ``tuple`` protocols are inherited as well:

        >>> period[0]
        'year'

        >>> period[0] in period
        True

        >>> len(period)
        3

        >>> period == Period((YEAR, start, 3))
        True

        >>> period > Period((YEAR, start, 3))
        False

        >>> unit, (year, month, day), size = period

    Since a period is a triple it can be used as a dictionary key.

    """

    plural: Callable[[str], str] = inflect.engine().plural

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}"
            f"({super(type(self), self).__repr__()})"
            )

    def __str__(self) -> str:
        """Transform period to a string.

        Returns:
            str: A string representation of the period.

        Examples:
            >>> from openfisca_core import periods

            >>> jan = periods.Instant((2021, 1, 1))
            >>> feb = jan.offset(1, MONTH)

            >>> str(Period((YEAR, jan, 1)))
            '2021'

            >>> str(Period((YEAR, feb, 1)))
            'year:2021-02'

            >>> str(Period((MONTH, feb, 1)))
            '2021-02'

            >>> str(Period((YEAR, jan, 2)))
            'year:2021:2'

            >>> str(Period((MONTH, jan, 2)))
            'month:2021-01:2'

            >>> str(Period((MONTH, jan, 12)))
            '2021'

        """

        unit, start, size = self

        if unit == ETERNITY:
            return "ETERNITY"

        year, month, day = start

        # 1 year long period
        if unit == MONTH and size == 12 or unit == YEAR and size == 1:
            if month == 1:
                # civil year starting from january
                return str(year)

            else:
                # rolling year
                return f"{YEAR}:{year}-{month:02d}"

        # simple month
        if unit == MONTH and size == 1:
            return f"{year}-{month:02d}"

        # several civil years
        if unit == YEAR and month == 1:
            return f"{unit}:{year}:{size}"

        if unit == DAY:
            if size == 1:
                return f"{year}-{month:02d}-{day:02d}"

            else:
                return f"{unit}:{year}-{month:02d}-{day:02d}:{size}"

        # complex period
        return f"{unit}:{year}-{month:02d}:{size}"

    def __contains__(self, other: object) -> bool:
        """Checks if a ``period`` contains another one.

        Args:
            other (object): The other ``Period``.

        Returns:
            True if ``other`` is contained, otherwise False.

        Example:
            >>> from openfisca_core import periods

            >>> start = periods.Instant((2021, 1, 1))
            >>> period = Period((YEAR, start, 1))
            >>> sub_period = Period((MONTH, start, 3))
            >>> sub_period in period
            True

        """

        if isinstance(other, Period):
            return self.start <= other.start and self.stop >= other.stop

        return super().__contains__(other)

    @property
    def unit(self) -> str:
        """The ``unit`` of the ``Period``.

        Returns:
            An int.

        Example:
            >>> from openfisca_core import periods

            >>> start = periods.Instant((2021, 10, 1))
            >>> period = Period((YEAR, start, 3))
            >>> period.unit
            'year'

        """

        return self[0]

    @property
    def start(self) -> Instant:
        """The ``Instant`` at which the ``Period`` starts.

        Returns:
            An Instant.

        Example:
            >>> from openfisca_core import periods

            >>> start = periods.Instant((2021, 10, 1))
            >>> period = Period((YEAR, start, 3))
            >>> period.start
            Instant((2021, 10, 1))

        """

        return self[1]

    @property
    def size(self) -> int:
        """The ``size`` of the ``Period``.

        Returns:
            An int.

        Example:
            >>> from openfisca_core import periods

            >>> start = periods.Instant((2021, 10, 1))
            >>> period = Period((YEAR, start, 3))
            >>> period.size
            3

        """

        return self[2]

    @property
    def stop(self) -> Instant:
        """Last day of the ``Period`` as an ``Instant``.

        Returns:
            An Instant.

        Raises:
            DateUnitValueError: If the period's unit isn't day, month or year.

        Examples:
            >>> from openfisca_core import periods

            >>> start = periods.Instant((2012, 2, 29))

            >>> Period((YEAR, start, 2)).stop
            Instant((2014, 2, 27))

            >>> Period((MONTH, start, 36)).stop
            Instant((2015, 2, 27))

            >>> Period((DAY, start, 1096)).stop
            Instant((2015, 2, 28))

        """

        unit, start, size = self

        if unit == ETERNITY:
            return type(self.start)((1, 1, 1))

        stop = (
            start
            .date()
            .add(**{self.plural(unit): size})
            .subtract(days = 1)
            )

        return type(start)((stop.year, stop.month, stop.day))

    def date(self) -> datetime.date:
        """The date representation of the ``period``'s' start date.

        Returns:
            A datetime.date.

        Raises:
            ValueError: If the period's size is greater than 1.

        Examples:
            >>> from openfisca_core import periods

            >>> start = periods.Instant((2021, 10, 1))

            >>> period = Period((YEAR, start, 1))
            >>> period.date()
            Date(2021, 10, 1)

            >>> period = Period((YEAR, start, 3))
            >>> period.date()
            Traceback (most recent call last):
            ValueError: 'date' undefined for period size > 1: year:2021-10:3.

        .. vesionchanged:: 39.0.0:
            Made it a normal method instead of a property.

        """

        if self.size > 1:
            raise ValueError(f"'date' undefined for period size > 1: {self}.")

        return self.start.date()

    def count(self, unit: str) -> int:
        """The ``size`` of the ``Period`` in the given unit.

        Args:
            unit: The unit to convert to.

        Returns:
            An int.

        Raises:
            ValueError: If the period's unit is not a day, a month or a year.

        Examples:
            >>> from openfisca_core import periods

            >>> start = periods.Instant((2021, 10, 1))

            >>> period = Period((YEAR, start, 3))
            >>> period.count(DAY)
            1096

            >>> period = Period((MONTH, start, 3))
            >>> period.count(DAY)
            92

            >>> period = Period((YEAR, start, 3))
            >>> period.count(MONTH)
            36

            >>> period = Period((DAY, start, 3))
            >>> period.count(MONTH)
            Traceback (most recent call last):
            ValueError: Cannot calculate number of months in day.

            >>> period = Period((YEAR, start, 3))
            >>> period.count(YEAR)
            3

            >>> period = Period((MONTH, start, 3))
            >>> period.count(YEAR)
            Traceback (most recent call last):
            ValueError: Cannot calculate number of years in month.

        .. versionadded:: 39.0.0

        """

        if unit == self.unit:
            return self.size

        if unit == DAY and self.unit in (MONTH, YEAR):
            return (self.stop.date() - self.start.date()).days + 1

        if unit == MONTH and self.unit == YEAR:
            return self.size * 12

        raise ValueError(f"Cannot calculate number of {unit} in {self.unit}.")

    def this(self, unit: str) -> Period:
        """A new month ``Period`` starting at the first of ``unit``.

        Args:
            unit: The unit of the requested Period.

        Returns:
            A Period.

        Examples:
            >>> from openfisca_core import periods

            >>> start = periods.Instant((2023, 1, 1))

            >>> period = Period((YEAR, start, 3))

            >>> period.this(DAY)
            Period(('day', Instant((2023, 1, 1)), 1))

            >>> period.this(MONTH)
            Period(('month', Instant((2023, 1, 1)), 1))

            >>> period.this(YEAR)
            Period(('year', Instant((2023, 1, 1)), 1))

        .. versionadded:: 39.0.0

        """

        return type(self)((unit, self.start.offset("first-of", unit), 1))


    def last(self, unit: str, size: int = 1) -> Period:
        """Last ``size`` ``unit``s of the ``Period``.

        Args:
            unit: The unit of the requested Period.
            size: The number of units to include in the Period.

        Returns:
            A Period.

        Examples:
            >>> from openfisca_core import periods

            >>> start = periods.Instant((2023, 1, 1))

            >>> period = Period((YEAR, start, 3))

            >>> period.last(DAY)
            Period(('day', Instant((2022, 12, 31)), 1))

            >>> period.last(DAY, 7)
            Period(('day', Instant((2022, 12, 25)), 7))

            >>> period.last(MONTH)
            Period(('month', Instant((2022, 12, 1)), 1))

            >>> period.last(MONTH, 3)
            Period(('month', Instant((2022, 10, 1)), 3))

            >>> period.last(YEAR)
            Period(('year', Instant((2022, 1, 1)), 1))

            >>> period.last(YEAR, 1)
            Period(('year', Instant((2022, 1, 1)), 1))

        .. versionadded:: 39.0.0

        """

        return type(self)((unit, self.ago(unit, size).start, size))

    def ago(self, unit: str, size: int = 1) -> Period:
        """``size`` ``unit``s ago of the ``Period``.

        Args:
            unit: The unit of the requested Period.
            size: The number of units ago.

        Returns:
            A Period.

        Examples:
            >>> from openfisca_core import periods

            >>> start = periods.Instant((2023, 1, 1))

            >>> period = Period((YEAR, start, 3))

            >>> period.ago(DAY)
            Period(('day', Instant((2022, 12, 31)), 1))

            >>> period.ago(DAY, 7)
            Period(('day', Instant((2022, 12, 25)), 1))

            >>> period.ago(MONTH)
            Period(('month', Instant((2022, 12, 1)), 1))

            >>> period.ago(MONTH, 3)
            Period(('month', Instant((2022, 10, 1)), 1))

            >>> period.ago(YEAR)
            Period(('year', Instant((2022, 1, 1)), 1))

            >>> period.ago(YEAR, 1)
            Period(('year', Instant((2022, 1, 1)), 1))

        .. versionadded:: 39.0.0

        """

        return type(self)((unit, self.this(unit).start, 1)).offset(-size)

    def offset(self, offset: str | int, unit: str | None = None) -> Period:
        """Increment (or decrement) the given period with offset units.

        Args:
            offset (str | int): How much of ``unit`` to offset.
            unit (str): What to offset.

        Returns:
            Period: A new one.

        Examples:
            >>> from openfisca_core import periods

            >>> start = periods.Instant((2014, 2, 3))

            >>> Period((DAY, start, 1)).offset("first-of", MONTH)
            Period(('day', Instant((2014, 2, 1)), 1))

            >>> Period((MONTH, start, 4)).offset("last-of", MONTH)
            Period(('month', Instant((2014, 2, 28)), 4))

            >>> start = periods.Instant((2021, 1, 1))

            >>> Period((DAY, start, 365)).offset(-3)
            Period(('day', Instant((2020, 12, 29)), 365))

            >>> Period((DAY, start, 365)).offset(1, YEAR)
            Period(('day', Instant((2022, 1, 1)), 365))

        """

        start = self[1].offset(offset, self[0] if unit is None else unit)

        return type(self)((self[0], start, self[2]))

    def subperiods(self, unit: str) -> Sequence[Period]:
        """Return the list of all the periods of unit ``unit``.

        Args:
            unit: A string representing period's ``unit``.

        Returns:
            A list of periods.

        Raises:
            DateUnitValueError: If the ``unit`` is not a valid date unit.
            ValueError: If the period's unit is smaller than the given unit.

        Examples:
            >>> from openfisca_core import periods

            >>> start = periods.Instant((2021, 1, 1))

            >>> period = Period((YEAR, start, 1))
            >>> period.subperiods(MONTH)
            [Period(('month', Instant((2021, 1, 1)), 1)),...2021, 12, 1)), 1))]

            >>> period = Period((YEAR, start, 2))
            >>> period.subperiods(YEAR)
            [Period(('year', Instant((2021, 1, 1)), 1)),...((2022, 1, 1)), 1))]

        .. versionchanged:: 39.0.0:
            Renamed from ``get_subperiods`` to ``subperiods``.

        """

        if UNIT_WEIGHTS[self.unit] < UNIT_WEIGHTS[unit]:
            raise ValueError(f"Cannot subdivide {self.unit} into {unit}")

        if unit not in (DAY, MONTH, YEAR):
            raise DateUnitValueError(unit)

        return [
            self.this(unit).offset(offset, unit)
            for offset in range(self.count(unit))
            ]
