from __future__ import annotations

from typing import Pattern

import re

from .domain._unit import DateUnit

# Matches "2015", "2015-01", "2015-01-01"
# Does not match "2015-13", "2015-12-32"
INSTANT_PATTERN: Pattern[str] = re.compile(r"^\d{4}(-(0[1-9]|1[012]))?(-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01]))?$")

UNIT_MAPPING = {
    1: DateUnit.YEAR,
    2: DateUnit.MONTH,
    3: DateUnit.DAY,
    }

UNIT_WEIGHTS = {
    DateUnit.DAY: 100,
    DateUnit.MONTH: 200,
    DateUnit.YEAR: 300,
    DateUnit.ETERNITY: 400,
    }
