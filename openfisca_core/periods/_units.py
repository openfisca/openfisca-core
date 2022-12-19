from __future__ import annotations

import enum

from ._exceptions import DateUnitValueError


class DateUnitMeta(enum.EnumMeta):
    """Metaclass for ``DateUnit``."""

    @property
    def isoformat(self) -> int:
        """Date units corresponding to the ISO format (day, month, and year).

        Returns:
            A DateUnit representing ISO format units.

        Examples:
            >>> DateUnit.isoformat
            <DateUnit.YEAR|MONTH|DAY: -9>

            >>> DateUnit.DAY in DateUnit.isoformat
            True

            >>> bool(DateUnit.DAY & DateUnit.isoformat)
            True

            >>> DateUnit.ETERNITY in DateUnit.isoformat
            False

            >>> bool(DateUnit.ETERNITY & DateUnit.isoformat)
            False

        .. versionadded:: 39.0.0

        """

        return ~DateUnit.ETERNITY


class DateUnit(enum.IntFlag, metaclass = DateUnitMeta):
    """The date units of a rule system.

    Examples:
        >>> repr(DateUnit)
        "<enum 'DateUnit'>"

        >>> repr(DateUnit.DAY)
        'day'

        >>> str(DateUnit.DAY)
        'day'

        >>> dict([(DateUnit.DAY, DateUnit.DAY.value)])
        {day: 1}

        >>> list(DateUnit)
        [day, month, year, eternity]

        >>> len(DateUnit)
        4

        >>> DateUnit["DAY"]
        day

        >>> DateUnit(DateUnit.DAY)
        day

        >>> DateUnit.DAY in DateUnit
        True

        >>> bool(DateUnit.DAY & ~DateUnit.ETERNITY)
        True

        >>> "DAY" in DateUnit
        False

        >>> DateUnit.DAY == 1
        True

        >>> DateUnit.DAY.name
        'DAY'

        >>> DateUnit.DAY.value
        1

    .. versionadded:: 39.0.0

    """

    #: The day unit.
    DAY = enum.auto()

    #: The month unit.
    MONTH = enum.auto()

    #: The year unit.
    YEAR = enum.auto()

    #: A special unit to represent time-independent properties.
    ETERNITY = enum.auto()

    def __repr__(self) -> str:
        try:
            return self.name.lower()

        except AttributeError:
            return super().__repr__()

    def __str__(self) -> str:
        try:
            return self.name.lower()

        except AttributeError:
            return super().__str__()

    @property
    def plural(self) -> str:
        """Returns the plural form of the date unit.

        Returns:
            str: The plural form.

        Raises:
            DateUnitValueError: When the date unit is not a ISO format unit.

        Examples:
            >>> DateUnit.DAY.plural
            'days'

            >>> DateUnit.ETERNITY.plural
            Traceback (most recent call last):
            DateUnitValueError: 'eternity' is not a valid ISO format date unit.

        .. versionadded:: 39.0.0

        """

        if self & type(self).isoformat:
            return str(self) + "s"

        raise DateUnitValueError(self)
