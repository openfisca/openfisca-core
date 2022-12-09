from __future__ import annotations

from typing import Dict

import collections

from openfisca_core import types

FilePath = str


class Files(collections.UserDict):
    """Dictionary of file paths by periods.

    Examples:
        >>> from openfisca_core import periods

        >>> instant = periods.Instant((2023, 1, 1))
        >>> period = periods.Period(("year", instant, 1))
        >>> path = "path/to/file.py"

        >>> Files({period: path})
        {Period(('year', Instant((2023, 1, 1)), 1)): 'path/to/file.py'}

    .. versionadded:: 37.1.0

    """

    data: Dict[types.Period, FilePath]
