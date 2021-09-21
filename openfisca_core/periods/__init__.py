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

from typing import Any, Dict

from .config import INSTANT_PATTERN, YEAR_OR_MONTH_OR_DAY_RE, DATE, LAST  # noqa: F401
from .instant_ import Instant  # noqa: F401
from .period_ import Period  # noqa: F401
from .date_unit import DateUnit  # noqa: F401

from .helpers import (  # noqa: F401
    N_,
    instant,
    instant_date,
    key_period_size,
    period,
    )

# For backwards compatibility

from .helpers import unit_weight, unit_weights  # noqa: F401

for item in DateUnit:
    globals()[item.name.upper()] = item.value

str_by_instant_cache: Dict[Any, Any] = {}
"""Cache to store :obj:`str` reprentations of :obj:`.Instant`.

.. deprecated:: 35.9.0
    This cache has been deprecated and will be removed in the future. The
    functionality is now provided by :func:`functools.lru_cache`.

"""

date_by_instant_cache: Dict[Any, Any] = {}
"""Cache to store :obj:`datetime.date` reprentations of :obj:`.Instant`.

.. deprecated:: 35.9.0
    This cache has been deprecated and will be removed in the future. The
    functionality is now provided by :func:`functools.lru_cache`.

"""

year_or_month_or_day_re = YEAR_OR_MONTH_OR_DAY_RE
"""???

.. deprecated:: 35.9.0
    ??? has been deprecated and it will be removed in 36.0.0.

"""
