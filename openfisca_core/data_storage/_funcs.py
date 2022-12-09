from __future__ import annotations

from openfisca_core import periods, types


def parse_period(value: types.Period, eternity: bool) -> types.Period:
    """Return a period.

    Args:
        value: Period-like value to be parsed.
        eternity: Whether to return the eternity period.

    Returns:
        A period.


    Examples:
        >>> instant = periods.Instant((2017, 1, 1))
        >>> period = periods.Period(("year", instant, 1))

        >>> parse_period(period, True)
        Period(('eternity', Instant((1, 1, 1)), inf))

        >>> parse_period(period, False)
        Period(('year', Instant((2017, 1, 1)), 1))

    .. versionadded:: 37.1.0

    """

    if eternity:
        return periods.period(periods.ETERNITY)

    if isinstance(value, types.Period):
        return value

    return periods.period(value)
