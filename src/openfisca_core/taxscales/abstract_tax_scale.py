from __future__ import annotations

import typing
import warnings

from openfisca_core.taxscales import TaxScaleLike

if typing.TYPE_CHECKING:
    import numpy

    NumericalArray = typing.Union[numpy.int_, numpy.float_]


class AbstractTaxScale(TaxScaleLike):
    """
    Base class for various types of tax scales: amount-based tax scales,
    rate-based tax scales...
    """

    def __init__(
            self,
            name: typing.Optional[str] = None,
            option: typing.Any = None,
            unit: numpy.int_ = None,
            ) -> None:

        message = [
            "The 'AbstractTaxScale' class has been deprecated since",
            "version 34.7.0, and will be removed in the future.",
            ]

        warnings.warn(" ".join(message), DeprecationWarning)
        super().__init__(name, option, unit)

    def __repr__(self) -> typing.NoReturn:
        raise NotImplementedError(
            "Method '__repr__' is not implemented for "
            f"{self.__class__.__name__}",
            )

    def calc(
            self,
            tax_base: NumericalArray,
            right: bool,
            ) -> typing.NoReturn:
        raise NotImplementedError(
            "Method 'calc' is not implemented for "
            f"{self.__class__.__name__}",
            )

    def to_dict(self) -> typing.NoReturn:
        raise NotImplementedError(
            f"Method 'to_dict' is not implemented for "
            f"{self.__class__.__name__}",
            )
