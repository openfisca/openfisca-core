import warnings

from .scales.average_rate_scale import AverageRateScale as AverageRateTaxScale  # noqa: F401
from .scales.helpers import combine_scales as combine_tax_scales  # noqa: F401
from .scales.marginal_amount_scale import MarginalAmountScale as MarginalAmountTaxScale  # noqa: F401
from .scales.marginal_rate_scale import MarginalRateScale as MarginalRateTaxScale  # noqa: F401
from .scales.rate_scale_like import RateScaleLike as RateScalTaxeLike  # noqa: F401
from .scales.scale_like import ScaleLike as ScalTaxeLike  # noqa: F401
from .scales.single_amount_scale import SingleAmountScale  # noqa: F401

message = [
    "taxscales submodule is deprecated since",
    "version 47.0.0, and will be removed in the future",
    "Please use scales.",
]
warnings.warn(" ".join(message), DeprecationWarning)
