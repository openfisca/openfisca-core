import calendar
import datetime
import functools
import re
from typing import Pattern

INSTANT_PATTERN: Pattern = re.compile(r"^\d{4}(-(0[1-9]|1[012]))?(-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01]))?$")
"""Pattern to validate a valid :obj:`.Instant`.

Matches: "2015", "2015-01", "2015-01-01"…
Does not match: "2015-13", "2015-12-32"…

"""

YEAR_OR_MONTH_OR_DAY_RE: Pattern = re.compile(r"(18|19|20)\d{2}(-(0?[1-9]|1[0-2])(-([0-2]?\d|3[0-1]))?)?$")
"""???

.. deprecated:: 35.9.0
    ??? has been deprecated and it will be removed in 36.0.0.

"""

DATE = functools.lru_cache(maxsize = None)(datetime.date)
"""A memoized date constructor."""

LAST = functools.lru_cache(maxsize = None)(calendar.monthrange)
"""A memoized date range constructor, useful for last-of month offsets."""
