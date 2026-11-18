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

from openfisca_core.errors import EmptyArgumentError  # noqa: F401

from .amount_scale_like import AmountScaleLike  # noqa: F401
from .average_rate_scale import AverageRateScale  # noqa: F401
from .helpers import combine_scales  # noqa: F401
from .marginal_amount_scale import MarginalAmountScale  # noqa: F401
from .marginal_rate_scale import MarginalRateScale  # noqa: F401
from .rate_scale_like import RateScaleLike  # noqa: F401
from .scale_like import ScaleLike  # noqa: F401
from .single_amount_scale import SingleAmountScale  # noqa: F401
