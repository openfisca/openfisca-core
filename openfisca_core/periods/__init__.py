"""Transitional imports to ensure non-breaking changes.

These imports could be deprecated in the next major release.

Currently, imports are used in the following way::
    from openfisca_core.module import symbol

This example causes cyclic dependency problems, which prevent us from
modularising the different components of the library and make them easier to
test and maintain.

After the next major release, imports could be used in the following way::
    from openfisca_core import module
    module.symbol()

And for classes::
    from openfisca_core.module import Symbol
    Symbol()

.. seealso:: `PEP8#Imports`_ and `OpenFisca's Styleguide`_.

.. _PEP8#Imports:
    https://www.python.org/dev/peps/pep-0008/#imports

.. _OpenFisca's Styleguide:
    https://github.com/openfisca/openfisca-core/blob/master/STYLEGUIDE.md

"""

from ._config import (  # noqa: F401
    DAY,
    MONTH,
    YEAR,
    ETERNITY,
    INSTANT_PATTERN,
    date_by_instant_cache,
    str_by_instant_cache,
    year_or_month_or_day_re,
    )

from ._funcs import (  # noqa: F401
    build_instant,
    build_period,
    instant_date,
    key_period_size,
    parse_simple_period,
    unit_weight,
    unit_weights,
    )

from .instant_ import Instant  # noqa: F401
from .period_ import Period  # noqa: F401
