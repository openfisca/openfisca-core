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

from ._dates import DateUnit
from .helpers import build_instant as instant
from .helpers import build_period as period
from .helpers import parse_instant_str as parse
from .instant_ import Instant
from .period_ import Period

DAY, MONTH, YEAR, ETERNITY = tuple(DateUnit)

# Deprecated

setattr(Period, "this_year", property(lambda self: self.first(YEAR)))  # noqa: B010
setattr(Period, "first_month", property(lambda self: self.first(MONTH)))  # noqa: B010
