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

from .abstract_rate_tax_scale import AbstractRateTaxScale  # noqa: F401
from .abstract_tax_scale import AbstractTaxScale  # noqa: F401
from .amount_tax_scale_like import AmountTaxScaleLike  # noqa: F401
from .helpers import combine_tax_scales  # noqa: F401
from .linear_average_rate_tax_scale import LinearAverageRateTaxScale  # noqa: F401
from .marginal_amount_tax_scale import MarginalAmountTaxScale  # noqa: F401
from .marginal_rate_tax_scale import MarginalRateTaxScale  # noqa: F401
from .rate_tax_scale_like import RateTaxScaleLike  # noqa: F401
from .single_amount_tax_scale import SingleAmountTaxScale  # noqa: F401
from .tax_scale_like import TaxScaleLike  # noqa: F401
