# Transitional imports to ensure non-breaking changes.
# Could be deprecated in the next major release.
#
# How imports are being used today:
#
#   >>> from policyengine_core.module import symbol
#
# The previous example provokes cyclic dependency problems
# that prevent us from modularizing the different components
# of the library so to make them easier to test and to maintain.
#
# How could them be used after the next major release:
#
#   >>> from policyengine_core import module
#   >>> module.symbol()
#
# And for classes:
#
#   >>> from policyengine_core.module import Symbol
#   >>> Symbol()
#
# See: https://www.python.org/dev/peps/pep-0008/#imports

from policyengine_core.errors import EmptyArgumentError

from .helpers import combine_tax_scales
from .tax_scale_like import TaxScaleLike
from .rate_tax_scale_like import RateTaxScaleLike
from .marginal_rate_tax_scale import MarginalRateTaxScale
from .linear_average_rate_tax_scale import (
    LinearAverageRateTaxScale,
)
from .abstract_tax_scale import AbstractTaxScale
from .amount_tax_scale_like import AmountTaxScaleLike
from .abstract_rate_tax_scale import AbstractRateTaxScale
from .marginal_amount_tax_scale import MarginalAmountTaxScale
from .single_amount_tax_scale import SingleAmountTaxScale
