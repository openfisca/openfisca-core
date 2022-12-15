from __future__ import annotations

from ._config import UNIT_WEIGHTS
from .typing import Period


def key_period_size(period: Period) -> str:
    """Define a key in order to sort periods by length.

    It uses two aspects: first, ``unit``, then, ``size``.

    Args:
        period (Period): A Period.

    Returns:
        str: A string.

    Examples:
        >>> from openfisca_core import periods

        >>> instant = periods.Instant((2021, 9, 14))

        >>> period = periods.Period((periods.DateUnit.DAY, instant, 1))
        >>> key_period_size(period)
        '100_1'

        >>> period = periods.Period((periods.DateUnit.YEAR, instant, 3))
        >>> key_period_size(period)
        '300_3'

    """

    unit, _start, size = period

    return f"{UNIT_WEIGHTS[unit]}_{size}"
