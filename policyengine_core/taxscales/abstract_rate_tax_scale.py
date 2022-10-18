from __future__ import annotations

import typing
import warnings

from policyengine_core.taxscales.rate_tax_scale_like import RateTaxScaleLike

if typing.TYPE_CHECKING:
    import numpy

    NumericalArray = typing.Union[numpy.int_, numpy.float_]


class AbstractRateTaxScale(RateTaxScaleLike):
    """
    Base class for various types of rate-based tax scales: marginal rate,
    linear average rate...
    """

    def __init__(
        self,
        name: typing.Optional[str] = None,
        option: typing.Any = None,
        unit: typing.Any = None,
    ) -> None:
        message = [
            "The 'AbstractRateTaxScale' class has been deprecated since",
            "version 34.7.0, and will be removed in the future.",
        ]

        warnings.warn(" ".join(message), DeprecationWarning)
        super().__init__(name, option, unit)

    def calc(
        self,
        tax_base: NumericalArray,
        right: bool,
    ) -> typing.NoReturn:
        raise NotImplementedError(
            "Method 'calc' is not implemented for "
            f"{self.__class__.__name__}",
        )
