# Transitional imports to ensure non-breaking changes.
# Could be deprecated in the next major release.
#
# How imports are being used today:
#
#   >>> from openfisca_core.module import symbol
#
# The previous example provokes cyclic dependency problems
# that prevent us from modularizing the different components
# of the library so to make them easier to test and to maintain.
#
# How could them be used after the next major release:
#
#   >>> from openfisca_core import module
#   >>> module.symbol()
#
# And for classes:
#
#   >>> from openfisca_core.module import Symbol
#   >>> Symbol()
#
# See: https://www.python.org/dev/peps/pep-0008/#imports

from . import types
from .config import (
    INSTANT_PATTERN,
    date_by_instant_cache,
    str_by_instant_cache,
    year_or_month_or_day_re,
)
from .date_unit import DateUnit
from .helpers import (
    instant,
    instant_date,
    key_period_size,
    period,
    unit_weight,
    unit_weights,
)
from .instant_ import Instant
from .period_ import Period

WEEKDAY = DateUnit.WEEKDAY
WEEK = DateUnit.WEEK
DAY = DateUnit.DAY
MONTH = DateUnit.MONTH
YEAR = DateUnit.YEAR
ETERNITY = DateUnit.ETERNITY
ISOFORMAT = DateUnit.isoformat
ISOCALENDAR = DateUnit.isocalendar

__all__ = [
    "INSTANT_PATTERN",
    "date_by_instant_cache",
    "str_by_instant_cache",
    "year_or_month_or_day_re",
    "DateUnit",
    "instant",
    "instant_date",
    "key_period_size",
    "period",
    "unit_weight",
    "unit_weights",
    "Instant",
    "Period",
    "WEEKDAY",
    "WEEK",
    "DAY",
    "MONTH",
    "YEAR",
    "ETERNITY",
    "ISOFORMAT",
    "ISOCALENDAR",
    "types",
]
