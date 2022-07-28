from __future__ import annotations

from typing import Dict, Pattern

import re

DAY = "day"
MONTH = "month"
YEAR = "year"
ETERNITY = "eternity"

# Matches "2015", "2015-01", "2015-01-01"
# Does not match "2015-13", "2015-12-32"
INSTANT_PATTERN: Pattern = re.compile(r"^\d{4}(-(0[1-9]|1[012]))?(-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01]))?$")

date_by_instant_cache: Dict = {}
str_by_instant_cache: Dict = {}
year_or_month_or_day_re: Pattern = re.compile(r'(18|19|20)\d{2}(-(0?[1-9]|1[0-2])(-([0-2]?\d|3[0-1]))?)?$')
