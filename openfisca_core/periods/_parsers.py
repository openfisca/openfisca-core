from __future__ import annotations

from typing import NamedTuple

import pendulum
from pendulum.datetime import Date
from pendulum.parsing import ParserError


class ISOFormat(NamedTuple):
    unit: int
    year: int
    month: int
    day: int
    shape: int

    @classmethod
    def parse(cls, value: str) -> ISOFormat | None:
        """Parse strings respecting the ISO format.

        Args:
            value: A string such as such as "2012" or "2015-03".

        Returns:
            An ISOFormat object if ``value`` is valid.
            None if ``value`` is not valid.

        Raises:
            AttributeError: When arguments are invalid, like ``"-1"``.
            ValueError: When values are invalid, like ``"2022-32-13"``.

        Examples:
            >>> ISOFormat.parse("ETERNITY")

            >>> ISOFormat.parse("2022")
            ISOFormat(unit=4, year=2022, month=1, day=1, shape=1)

            >>> ISOFormat.parse("2022-02")
            ISOFormat(unit=2, year=2022, month=2, day=1, shape=2)

            >>> ISOFormat.parse("2022-02-13")
            ISOFormat(unit=1, year=2022, month=2, day=13, shape=3)

        .. versionadded:: 39.0.0

        """

        # If it's a complex period, next!
        if len(value.split(":")) != 1:
            return None

        # Check for a non-empty string.
        if not value and not isinstance(value, str):
            raise AttributeError

        # If it's negative period, next!
        if value[0] == "-" or len(value.split(":")) != 1:
            raise ValueError

        try:
            date = pendulum.parse(value, exact = True)

        except ParserError:
            return None

        if not isinstance(date, Date):
            raise ValueError

        # We get the shape of the string (e.g. "2012-02" = 2)
        shape = len(value.split("-"))

        # We get the unit from the shape (e.g. 2 = "month")
        unit = pow(2, 3 - shape)

        # We build the corresponding ISOFormat object
        return cls(unit, date.year, date.month, date.day, shape)
