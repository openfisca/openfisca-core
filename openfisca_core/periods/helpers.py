from typing import Dict, NoReturn, Optional

import datetime
import os

import pendulum
from pendulum.parsing import ParserError

from . import _parsers, config
from .date_unit import DateUnit
from .instant_ import Instant
from .period_ import Period


def instant(instant) -> Optional[Instant]:
    """Build a new instant, aka a triple of integers (year, month, day).

    Args:
        instant: An ``instant-like`` object.

    Returns:
        None: When ``instant`` is None.
        :obj:`.Instant`: Otherwise.

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

    """

    if instant is None:
        return None
    if isinstance(instant, Instant):
        return instant
    if isinstance(instant, str):
        if not config.INSTANT_PATTERN.match(instant):
            raise ValueError(
                f"'{instant}' is not a valid instant. Instants are described using the 'YYYY-MM-DD' format, for instance '2015-06-15'."
            )
        instant = Instant(int(fragment) for fragment in instant.split("-", 2)[:3])
    elif isinstance(instant, datetime.date):
        instant = Instant((instant.year, instant.month, instant.day))
    elif isinstance(instant, int):
        instant = (instant,)
    elif isinstance(instant, list):
        assert 1 <= len(instant) <= 3
        instant = tuple(instant)
    elif isinstance(instant, Period):
        instant = instant.start
    else:
        assert isinstance(instant, tuple), instant
        assert 1 <= len(instant) <= 3
    if len(instant) == 1:
        return Instant((instant[0], 1, 1))
    if len(instant) == 2:
        return Instant((instant[0], instant[1], 1))
    return Instant(instant)


def instant_date(instant: Optional[Instant]) -> Optional[datetime.date]:
    """Returns the date representation of an :class:`.Instant`.

    Args:
        instant (:obj:`.Instant`, optional):

    Returns:
        None: When ``instant`` is None.
        :obj:`datetime.date`: Otherwise.

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


def period(value) -> Period:
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
        Period((<DateUnit.ETERNITY: 'eternity'>, Instant((1, 1, 1)), inf))

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

    if isinstance(value, Period):
        return value

    # We return a "day-period", for example
    # ``<Period(('day', <Instant(2021, 1, 1)>, 1))>``.
    if isinstance(value, Instant):
        return Period((DateUnit.DAY, value, 1))

    # For example ``datetime.date(2021, 9, 16)``.
    if isinstance(value, datetime.date):
        return Period((DateUnit.DAY, instant(value), 1))

    # We return an "eternity-period", for example
    # ``<Period(('eternity', <Instant(1, 1, 1)>, inf))>``.
    if str(value).lower() == DateUnit.ETERNITY:
        return Period(
            (
                DateUnit.ETERNITY,
                instant(datetime.date.min),
                float("inf"),
            )
        )

    # For example ``2021`` gives
    # ``<Period(('year', <Instant(2021, 1, 1)>, 1))>``.
    if isinstance(value, int):
        return Period((DateUnit.YEAR, instant(value), 1))

    # Up to this point, if ``value`` is not a :obj:`str`, we desist.
    if not isinstance(value, str):
        _raise_error(value)

    # There can't be empty strings.
    if not value:
        _raise_error(value)

    # Try to parse from an ISO format/calendar period.
    try:
        period = _parsers._parse_period(value)

    except (AttributeError, ParserError, ValueError):
        _raise_error(value)

    if period is not None:
        return period

    # A complex period has a ':' in its string.
    if ":" not in value:
        _raise_error(value)

    components = value.split(":")

    # left-most component must be a valid unit
    unit = components[0]

    if unit not in list(DateUnit) or unit == DateUnit.ETERNITY:
        _raise_error(value)

    # Cast ``unit`` to DateUnit.
    unit = DateUnit(unit)

    # middle component must be a valid iso period
    try:
        base_period = _parsers._parse_period(components[1])

    except (AttributeError, ParserError, ValueError):
        _raise_error(value)

    if not base_period:
        _raise_error(value)

    # period like year:2015-03 have a size of 1
    if len(components) == 2:
        size = 1

    # if provided, make sure the size is an integer
    elif len(components) == 3:
        try:
            size = int(components[2])

        except ValueError:
            _raise_error(value)

    # if there is more than 2 ":" in the string, the period is invalid
    else:
        _raise_error(value)

    # reject ambiguous periods such as month:2014
    if unit_weight(base_period.unit) > unit_weight(unit):
        _raise_error(value)

    return Period((unit, base_period.start, size))


def _raise_error(value: str) -> NoReturn:
    """Raise an error.

    Examples:
        >>> _raise_error("Oi mate!")
        Traceback (most recent call last):
        ValueError: Expected a period (eg. '2017', '2017-01', '2017-01-01', ...
        Learn more about legal period formats in OpenFisca:
        <https://openfisca.org/doc/coding-the-legislation/35_periods.html#pe...

    """

    message = os.linesep.join(
        [
            f"Expected a period (eg. '2017', '2017-01', '2017-01-01', ...); got: '{value}'.",
            "Learn more about legal period formats in OpenFisca:",
            "<https://openfisca.org/doc/coding-the-legislation/35_periods.html#periods-in-simulations>.",
        ]
    )
    raise ValueError(message)


def key_period_size(period: Period) -> str:
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

    unit, start, size = period

    return f"{unit_weight(unit)}_{size}"


def unit_weights() -> dict[str, int]:
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


def unit_weight(unit: str) -> int:
    """Retrieves a specific date unit weight.

    Examples:
        >>> unit_weight(DateUnit.DAY)
        100

    """

    return unit_weights()[unit]
