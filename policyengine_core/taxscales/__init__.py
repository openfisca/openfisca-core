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
