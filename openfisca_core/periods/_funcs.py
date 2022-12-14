from __future__ import annotations

from typing import Any, Dict, NoReturn, Optional

import datetime
import os

from openfisca_core import types

from .. import periods


def build_instant(value: Any) -> Optional[types.Instant]:
    """Build a new instant, aka a triple of integers (year, month, day).

    Args:
        value: An ``instant-like`` object.

    Returns:
        None: When ``instant`` is None.
        :obj:`.Instant`: Otherwise.

    Raises:
        ValueError: When the arguments were invalid, like "2021-32-13".

    Examples:
        >>> build_instant(datetime.date(2021, 9, 16))
        Instant((2021, 9, 16))

        >>> build_instant(periods.Instant((2021, 9, 16)))
        Instant((2021, 9, 16))

        >>> build_instant(periods.Period(("year", periods.Instant((2021, 9, 16)), 1)))
        Instant((2021, 9, 16))

        >>> build_instant("2021")
        Instant((2021, 1, 1))

        >>> build_instant(2021)
        Instant((2021, 1, 1))

        >>> build_instant((2021, 9))
        Instant((2021, 9, 1))

    """

    if value is None:
        return None

    if isinstance(value, periods.Instant):
        return value

    if isinstance(value, str):
        if not periods.INSTANT_PATTERN.match(value):
            raise ValueError(
                f"'{value}' is not a valid instant. Instants are described"
                "using the 'YYYY-MM-DD' format, for instance '2015-06-15'."
                )

        instant = periods.Instant(
            int(fragment)
            for fragment in value.split('-', 2)[:3]
            )

    elif isinstance(value, datetime.date):
        instant = periods.Instant((value.year, value.month, value.day))

    elif isinstance(value, int):
        instant = (value,)

    elif isinstance(value, list):
        assert 1 <= len(value) <= 3
        instant = tuple(value)

    elif isinstance(value, periods.Period):
        instant = value.start

    else:
        assert isinstance(value, tuple), value
        assert 1 <= len(value) <= 3
        instant = value

    if len(instant) == 1:
        return periods.Instant((instant[0], 1, 1))

    if len(instant) == 2:
        return periods.Instant((instant[0], instant[1], 1))

    return periods.Instant(instant)


def build_period(value: Any) -> types.Period:
    """Build a new period, aka a triple (unit, start_instant, size).

    Args:
        value: A ``period-like`` object.

    Returns:
        :obj:`.Period`: A period.

    Raises:
        :exc:`ValueError`: When the arguments were invalid, like "2021-32-13".

    Examples:
        >>> build_period(periods.Period(("year", periods.Instant((2021, 1, 1)), 1)))
        Period(('year', Instant((2021, 1, 1)), 1))

        >>> build_period(periods.Instant((2021, 1, 1)))
        Period(('day', Instant((2021, 1, 1)), 1))

        >>> build_period("eternity")
        Period(('eternity', Instant((1, 1, 1)), inf))

        >>> build_period(2021)
        Period(('year', Instant((2021, 1, 1)), 1))

        >>> build_period("2014")
        Period(('year', Instant((2014, 1, 1)), 1))

        >>> build_period("year:2014")
        Period(('year', Instant((2014, 1, 1)), 1))

        >>> build_period("month:2014-2")
        Period(('month', Instant((2014, 2, 1)), 1))

        >>> build_period("year:2014-2")
        Period(('year', Instant((2014, 2, 1)), 1))

        >>> build_period("day:2014-2-2")
        Period(('day', Instant((2014, 2, 2)), 1))

        >>> build_period("day:2014-2-2:3")
        Period(('day', Instant((2014, 2, 2)), 3))

    """

    if isinstance(value, periods.Period):
        return value

    if isinstance(value, periods.Instant):
        return periods.Period((periods.DAY, value, 1))

    if value == "ETERNITY" or value == periods.ETERNITY:
        return periods.Period(("eternity", build_instant(datetime.date.min), float("inf")))

    if isinstance(value, int):
        return periods.Period((periods.YEAR, periods.Instant((value, 1, 1)), 1))

    if not isinstance(value, str):
        _raise_error(value)

    # Try to parse as a simple period
    period = parse_simple_period(value)

    if period is not None:
        return period

    # Complex periods must have a ':' in their strings
    if ":" not in value:
        _raise_error(value)

    components = value.split(":")

    # Left-most component must be a valid unit
    unit = components[0]

    if unit not in (periods.DAY, periods.MONTH, periods.YEAR):
        _raise_error(value)

    # Middle component must be a valid iso period
    base_period = parse_simple_period(components[1])

    if not base_period:
        _raise_error(value)

    # Periods like year:2015-03 have a size of 1
    if len(components) == 2:
        size = 1

    # If provided, make sure the size is an integer
    elif len(components) == 3:
        try:
            size = int(components[2])

        except ValueError:
            _raise_error(value)

    # If there are more than 2 ":" in the string, the period is invalid
    else:
        _raise_error(value)

    # Reject ambiguous periods such as month:2014
    if unit_weight(base_period.unit) > unit_weight(unit):
        _raise_error(value)

    return periods.Period((unit, base_period.start, size))


def key_period_size(period: types.Period) -> str:
    """Define a key in order to sort periods by length.

    It uses two aspects: first, ``unit``, then, ``size``.

    Args:
        period: An :mod:`.openfisca_core` :obj:`.Period`.

    Returns:
        :obj:`str`: A string.

    Examples:
        >>> instant = periods.Instant((2021, 9, 14))

        >>> period = periods.Period(("day", instant, 1))
        >>> key_period_size(period)
        '100_1'

        >>> period = periods.Period(("year", instant, 3))
        >>> key_period_size(period)
        '300_3'

    """

    unit, start, size = period

    return f"{unit_weight(unit)}_{size}"


def parse_simple_period(value: str) -> Optional[types.Period]:
    """Parse simple periods respecting the ISO format.

    Such as "2012" or "2015-03".

    Examples:
        >>> parse_simple_period("2022")
        Period(('year', Instant((2022, 1, 1)), 1))

        >>> parse_simple_period("2022-02")
        Period(('month', Instant((2022, 2, 1)), 1))

        >>> parse_simple_period("2022-02-13")
        Period(('day', Instant((2022, 2, 13)), 1))

    """

    try:
        date = datetime.datetime.strptime(value, '%Y')

    except ValueError:
        try:
            date = datetime.datetime.strptime(value, '%Y-%m')

        except ValueError:
            try:
                date = datetime.datetime.strptime(value, '%Y-%m-%d')

            except ValueError:
                return None

            else:
                return periods.Period((periods.DAY, periods.Instant((date.year, date.month, date.day)), 1))

        else:
            return periods.Period((periods.MONTH, periods.Instant((date.year, date.month, 1)), 1))

    else:
        return periods.Period((periods.YEAR, periods.Instant((date.year, date.month, 1)), 1))


def unit_weights() -> Dict[str, int]:
    """Assign weights to date units.

    Examples:
        >>> unit_weights()
        {'day': 100, ...}

    """

    return {
        periods.DAY: 100,
        periods.MONTH: 200,
        periods.YEAR: 300,
        periods.ETERNITY: 400,
        }


def unit_weight(unit: str) -> int:
    """Retrieves a specific date unit weight.

    Examples:
        >>> unit_weight("day")
        100

    """

    return unit_weights()[unit]


def _raise_error(value: str) -> NoReturn:
    """Raise an error.

    Examples:
        >>> _raise_error("Oi mate!")
        Traceback (most recent call last):
        ValueError: Expected a period (eg. '2017', '2017-01', '2017-01-01', ...); got:
        'Oi mate!'. Learn more about legal period formats in OpenFisca:
        <https://openfisca.org/doc/coding-the-legislation/35_periods.html#periods-in-simulations>.

    """

    message = os.linesep.join([
        "Expected a period (eg. '2017', '2017-01', '2017-01-01', ...); got:",
        f"'{value}'. Learn more about legal period formats in OpenFisca:",
        "<https://openfisca.org/doc/coding-the-legislation/35_periods.html#periods-in-simulations>."
        ])

    raise ValueError(message)
