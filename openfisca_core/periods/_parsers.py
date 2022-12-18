from __future__ import annotations

from typing import NamedTuple, Sequence

import pendulum
from pendulum.datetime import Date
from pendulum.parsing import ParserError


class ISOFormat(NamedTuple):
    """An implementation of the `parse` protocol."""

    #: The year of the parsed period.
    year: int

    #: The month of the parsed period.
    month: int

    #: The month of the parsed period.
    day: int

    #: The unit of the parsed period, in binary.
    unit: int

    #: The number of fragments in the parsed period.
    shape: int

    @classmethod
    def fromint(cls, value: int) -> ISOFormat | None:
        """Parse an int respecting the ISO format.

        Args:
            value: The integer to parse.

        Returns:
            An ISOFormat object if ``value`` is valid.
            None otherwise.

        Examples:
            >>> ISOFormat.fromint(1)
            ISOFormat(year=1, month=1, day=1, unit=4, shape=1)

            >>> ISOFormat.fromint(2023)
            ISOFormat(year=2023, month=1, day=1, unit=4, shape=1)

            >>> ISOFormat.fromint(-1)

            >>> ISOFormat.fromint("2023")

            >>> ISOFormat.fromint(20231231)

        .. versionadded:: 39.0.0

        """

        if not isinstance(value, int):
            return None

        if not 1 <= len(str(value)) <= 4:
            return None

        try:
            if not 1 <= int(str(value)[:4]) < 10000:
                return None

        except ValueError:
            return None

        return cls(value, 1, 1, 4, 1)

    @classmethod
    def fromstr(cls, value: str) -> ISOFormat | None:
        """Parse strings respecting the ISO format.

        Args:
            value: A string such as such as "2012" or "2015-03".

        Returns:
            An ISOFormat object if ``value`` is valid.
            None if ``value`` is not valid.

        Examples:
            >>> ISOFormat.fromstr("2022")
            ISOFormat(year=2022, month=1, day=1, unit=4, shape=1)

            >>> ISOFormat.fromstr("2022-02")
            ISOFormat(year=2022, month=2, day=1, unit=2, shape=2)

            >>> ISOFormat.fromstr("2022-02-13")
            ISOFormat(year=2022, month=2, day=13, unit=1, shape=3)

            >>> ISOFormat.fromstr(1000)

            >>> ISOFormat.fromstr("ETERNITY")

        .. versionadded:: 39.0.0

        """

        if not isinstance(value, str):
            return None

        if not value:
            return None

        # If it is a complex value, next!
        if len(value.split(":")) != 1:
            return None

        # If it's negative period, next!
        if value[0] == "-":
            return None

        try:
            # We parse the date
            date = pendulum.parse(value, exact = True, strict = True)

        except ParserError:
            return None

        if not isinstance(date, Date):
            return None

        # We get the shape of the string (e.g. "2012-02" = 2)
        shape = len(value.split("-"))

        # We get the unit from the shape (e.g. 2 = "month")
        unit = pow(2, 3 - shape)

        # We build the corresponding ISOFormat object
        return cls(date.year, date.month, date.day, unit, shape)

    @classmethod
    def fromseq(cls, value: Sequence[int]) -> ISOFormat | None:
        """Parse a sequence of ints respecting the ISO format.

        Args:
            value: A sequence of ints such as [2012, 3, 13].

        Returns:
            An ISOFormat object if ``value`` is valid.
            None if ``value`` is not valid.

        Examples:
            >>> ISOFormat.fromseq([2022])
            ISOFormat(year=2022, month=1, day=1, unit=4, shape=1)

            >>> ISOFormat.fromseq([2022, 1])
            ISOFormat(year=2022, month=1, day=1, unit=2, shape=2)

            >>> ISOFormat.fromseq([2022, 1, 1])
            ISOFormat(year=2022, month=1, day=1, unit=1, shape=3)

            >>> ISOFormat.fromseq([-2022, 1, 1])

            >>> ISOFormat.fromseq([2022, 13, 1])

            >>> ISOFormat.fromseq([2022, 1, 32])

        .. versionadded:: 39.0.0

        """

        if not isinstance(value, (list, tuple)):
            return None

        if not value:
            return None

        if not 1 <= len(value) <= 3:
            return None

        if not all(isinstance(unit, int) for unit in value):
            return None

        if not all(unit == abs(unit) for unit in value):
            return None

        # We get the shape of the string (e.g. "2012-02" = 2)
        shape = len(value)

        # We get the unit from the shape (e.g. 2 = "month")
        unit = pow(2, 3 - shape)

        while len(value) < 3:
            value = (*value, 1)

        try:
            # We parse the date
            date = pendulum.date(*value)

        except ValueError:
            return None

        if not isinstance(date, Date):
            return None

        # We build the corresponding ISOFormat object
        return cls(date.year, date.month, date.day, unit, shape)
