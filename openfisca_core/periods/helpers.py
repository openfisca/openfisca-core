from __future__ import annotations

from typing import NoReturn

import datetime
import functools

import pendulum

from . import config, types as t
from ._errors import InstantError, PeriodError
from ._parsers import parse_instant, parse_period
from .date_unit import DateUnit
from .instant_ import Instant
from .period_ import Period


@functools.singledispatch
def instant(value: object) -> t.Instant:
    """Build a new instant, aka a triple of integers (year, month, day).

    Args:
        value(object): An ``instant-like`` object.

    Returns:
        :obj:`.Instant`: A new instant.

    Raises:
        :exc:`ValueError`: When the arguments were invalid, like "2021-32-13".

    Examples:
        >>> instant((2021,))
        Instant((2021, 1, 1))

        >>> instant((2021, 9))
        Instant((2021, 9, 1))

        >>> instant(datetime.date(2021, 9, 16))
        Instant((2021, 9, 16))

        >>> instant(Instant((2021, 9, 16)))
        Instant((2021, 9, 16))

        >>> instant(Period((DateUnit.YEAR, Instant((2021, 9, 16)), 1)))
        Instant((2021, 9, 16))

        >>> instant(2021)
        Instant((2021, 1, 1))

        >>> instant("2021")
        Instant((2021, 1, 1))

        >>> instant([2021])
        Instant((2021, 1, 1))

        >>> instant([2021, 9])
        Instant((2021, 9, 1))

        >>> instant(None)
        Traceback (most recent call last):
        openfisca_core.periods._errors.InstantError: 'None' is not a valid i...

    """

    if isinstance(value, t.SeqInt):
        return Instant((list(value) + [1] * 3)[:3])

    raise InstantError(str(value))


@instant.register
def _(value: None) -> NoReturn:
    raise InstantError(str(value))


@instant.register
def _(value: int) -> t.Instant:
    return Instant((value, 1, 1))


@instant.register
def _(value: Period) -> t.Instant:
    return value.start


@instant.register
def _(value: t.Instant) -> t.Instant:
    return value


@instant.register
def _(value: datetime.date) -> t.Instant:
    return Instant((value.year, value.month, value.day))


@instant.register
def _(value: str) -> t.Instant:
    return parse_instant(value)


def instant_date(instant: None | t.Instant) -> None | datetime.date:
    """Returns the date representation of an ``Instant``.

    Args:
        instant: An ``Instant``.

    Returns:
        None: When ``instant`` is None.
        datetime.date: Otherwise.

    Examples:
        >>> instant_date(Instant((2021, 1, 1)))
        Date(2021, 1, 1)

    """
    if instant is None:
        return None

    instant_date = config.date_by_instant_cache.get(instant)

    if instant_date is None:
        config.date_by_instant_cache[instant] = instant_date = pendulum.date(*instant)

    return instant_date


@functools.singledispatch
def period(value: object) -> t.Period:
    """Build a new period, aka a triple (unit, start_instant, size).

    Args:
        value: A ``period-like`` object.

    Returns:
        :obj:`.Period`: A period.

    Raises:
        :exc:`ValueError`: When the arguments were invalid, like "2021-32-13".

    Examples:
        >>> period(Period((DateUnit.YEAR, Instant((2021, 1, 1)), 1)))
        Period((<DateUnit.YEAR: 'year'>, Instant((2021, 1, 1)), 1))

        >>> period(Instant((2021, 1, 1)))
        Period((<DateUnit.DAY: 'day'>, Instant((2021, 1, 1)), 1))

        >>> period(DateUnit.ETERNITY)
        Period((<DateUnit.ETERNITY: 'eternity'>, Instant((-1, -1, -1)), -1))

        >>> period(2021)
        Period((<DateUnit.YEAR: 'year'>, Instant((2021, 1, 1)), 1))

        >>> period("2014")
        Period((<DateUnit.YEAR: 'year'>, Instant((2014, 1, 1)), 1))

        >>> period("year:2014")
        Period((<DateUnit.YEAR: 'year'>, Instant((2014, 1, 1)), 1))

        >>> period("month:2014-02")
        Period((<DateUnit.MONTH: 'month'>, Instant((2014, 2, 1)), 1))

        >>> period("year:2014-02")
        Period((<DateUnit.YEAR: 'year'>, Instant((2014, 2, 1)), 1))

        >>> period("day:2014-02-02")
        Period((<DateUnit.DAY: 'day'>, Instant((2014, 2, 2)), 1))

        >>> period("day:2014-02-02:3")
        Period((<DateUnit.DAY: 'day'>, Instant((2014, 2, 2)), 3))

    """

    one, two, three = 1, 2, 3

    # We return an "eternity-period", for example
    # ``<Period(('eternity', <Instant(-1, -1, -1)>, -1))>``.
    if str(value).lower() == DateUnit.ETERNITY:
        return Period.eternity()

    # We try to parse from an ISO format/calendar period.
    if isinstance(value, t.InstantStr):
        return parse_period(value)

    # A complex period has a ':' in its string.
    if isinstance(value, t.PeriodStr):
        components = value.split(":")

        # The left-most component must be a valid unit
        unit = components[0]

        if unit not in list(DateUnit) or unit == DateUnit.ETERNITY:
            raise PeriodError(str(value))

        # Cast ``unit`` to DateUnit.
        unit = DateUnit(unit)

        # The middle component must be a valid iso period
        period = parse_period(components[1])

        # Periods like year:2015-03 have a size of 1
        if len(components) == two:
            size = one

        # if provided, make sure the size is an integer
        elif len(components) == three:
            try:
                size = int(components[2])

            except ValueError as error:
                raise PeriodError(str(value)) from error

        # If there are more than 2 ":" in the string, the period is invalid
        else:
            raise PeriodError(str(value))

        # Reject ambiguous periods such as month:2014
        if unit_weight(period.unit) > unit_weight(unit):
            raise PeriodError(str(value))

        return Period((unit, period.start, size))

    raise PeriodError(str(value))


@period.register
def _(value: None) -> NoReturn:
    raise PeriodError(str(value))


@period.register
def _(value: int) -> t.Period:
    return Period((DateUnit.YEAR, instant(value), 1))


@period.register
def _(value: t.Period) -> t.Period:
    return value


@period.register
def _(value: t.Instant) -> t.Period:
    return Period((DateUnit.DAY, value, 1))


@period.register
def _(value: datetime.date) -> t.Period:
    return Period((DateUnit.DAY, instant(value), 1))


def key_period_size(period: t.Period) -> str:
    """Define a key in order to sort periods by length.

    It uses two aspects: first, ``unit``, then, ``size``.

    Args:
        period: An :mod:`.openfisca_core` :obj:`.Period`.

    Returns:
        :obj:`str`: A string.

    Examples:
        >>> instant = Instant((2021, 9, 14))

        >>> period = Period((DateUnit.DAY, instant, 1))
        >>> key_period_size(period)
        '100_1'

        >>> period = Period((DateUnit.YEAR, instant, 3))
        >>> key_period_size(period)
        '300_3'

    """

    return f"{unit_weight(period.unit)}_{period.size}"


def unit_weights() -> dict[t.DateUnit, int]:
    """Assign weights to date units.

    Examples:
        >>> unit_weights()
        {<DateUnit.WEEKDAY: 'weekday'>: 100, ...ETERNITY: 'eternity'>: 400}

    """
    return {
        DateUnit.WEEKDAY: 100,
        DateUnit.WEEK: 200,
        DateUnit.DAY: 100,
        DateUnit.MONTH: 200,
        DateUnit.YEAR: 300,
        DateUnit.ETERNITY: 400,
    }


def unit_weight(unit: t.DateUnit) -> int:
    """Retrieves a specific date unit weight.

    Examples:
        >>> unit_weight(DateUnit.DAY)
        100

    """
    return unit_weights()[unit]


__all__ = [
    "instant",
    "instant_date",
    "key_period_size",
    "period",
    "unit_weight",
    "unit_weights",
]
