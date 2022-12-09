from __future__ import annotations

from typing import Dict

import collections

import numpy

from openfisca_core import types


class Arrays(collections.UserDict):
    """Dictionary of calculated vectors by period.

    Examples:
        >>> from openfisca_core import periods

        >>> instant = periods.Instant((2023, 1, 1))
        >>> period = periods.Period(("year", instant, 1))
        >>> vector = numpy.array([1])

        >>> Arrays({period: vector})
        {Period(('year', Instant((2023, 1, 1)), 1)): array([1])}

    .. versionadded:: 37.1.0

    """

    data: Dict[types.Period, numpy.ndarray]
