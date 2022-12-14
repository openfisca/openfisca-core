from __future__ import annotations

from typing import Pattern

import re

# Matches "2015", "2015-01", "2015-01-01"
# Does not match "2015-13", "2015-12-32"
INSTANT_PATTERN: Pattern = re.compile(r"^\d{4}(-(0[1-9]|1[012]))?(-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01]))?$")
