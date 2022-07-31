import datetime
from typing import Optional

from .date_unit import DateUnit
from .instant_ import Instant
from .period_ import Period


def _from_isoformat(value: str) -> Optional[Period]:
    """Parses ISO format periods.

    Such as "2012" or "2015-03".

    Examples:
        >>> _from_isoformat("2022")
        Period((<DateUnit.YEAR: 'year'>, Instant((2022, 1, 1)), 1))

        >>> _from_isoformat("2022-02")
        Period((<DateUnit.MONTH: 'month'>, Instant((2022, 2, 1)), 1))

        >>> _from_isoformat("2022-02-13")
        Period((<DateUnit.DAY: 'day'>, Instant((2022, 2, 13)), 1))

    """

    # If it's complex, next!
    if len(value.split(":")) != 1:
        return None

    # If there are weeks, next!
    if value.find("W") != -1:
        return None

    # If it's just a year...
    if len(value.split("-")) == 1:
        try:
            date = datetime.date(int(value), 1, 1)

            return Period((
                DateUnit.YEAR,
                Instant((date.year, 1, 1)),
                1,
                ))

        except ValueError:
            return None

    try:
        components = list(map(int, value.split("-")))

    except ValueError:
        return None

    if len(components) == 2:
        try:
            year, month = components
            date = datetime.date(year, month, 1)

            return Period((
                DateUnit.MONTH,
                Instant((date.year, date.month, 1)),
                1,
                ))

        except ValueError:
            return None

    if len(components) == 3:
        try:
            year, month, day = components
            date = datetime.date(year, month, day)

            return Period((
                DateUnit.DAY,
                Instant((date.year, date.month, date.day)),
                1,
                ))

        except ValueError:
            return None

    return None


def _from_isocalendar(value: str) -> Optional[Period]:
    """Parses ISO calendar periods.

    Such as "2010-W3" or "2012-W5-7".

    Examples:
        >>> _from_isocalendar("2022")

        >>> _from_isocalendar("2022-W3")
        Period((<DateUnit.WEEK: 'week'>, Instant((2022, 1, 17)), 1))

        >>> _from_isocalendar("2022-W9-3")
        Period((<DateUnit.WEEKDAY: 'weekday'>, Instant((2022, 3, 2)), 1))

    """

    # If it's complex, next!
    if len(value.split(":")) != 1:
        return None

    # If it's just a year, next!
    if len(value.split("-")) == 1:
        return None

    # If there are no weeks, next!
    if value.find("W") == -1:
        return None

    try:
        value = value.replace("W", "")
        components = list(map(int, value.split("-")))

    except ValueError:
        return None

    # If it has no weekdays return a week period.
    if len(components) == 2:
        try:
            year, week = components
            date = datetime.date.fromisocalendar(year, week, 1)

            return Period((
                DateUnit.WEEK,
                Instant((date.year, date.month, date.day)),
                1,
                ))

        except ValueError:
            return None

    # If it has weekdays return a weekday period
    if len(components) == 3:
        try:
            year, week, weekday = components
            date = datetime.date.fromisocalendar(year, week, weekday)
            return Period((
                DateUnit.WEEKDAY,
                Instant((date.year, date.month, date.day)),
                1,
                ))

        except ValueError:
            return None

    return None
