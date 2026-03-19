from __future__ import annotations

import typing

import warnings

from .tax_scale_like import TaxScaleLike

if typing.TYPE_CHECKING:
    import numpy

    NumericalArray = typing.Union[numpy.int32, numpy.float32]


class AbstractTaxScale(TaxScaleLike):
    """Base class for various types of tax scales: amount-based tax scales,
    rate-based tax scales...
    """

    def __init__(
        self,
        name: str | None = None,
        option: typing.Any = None,
        unit: numpy.int16 = None,
    ) -> None:
        message = [
            "The 'AbstractTaxScale' class has been deprecated since",
            "version 34.7.0, and will be removed in the future.",
        ]

        warnings.warn(" ".join(message), DeprecationWarning, stacklevel=2)
        super().__init__(name, option, unit)

    def __repr__(self) -> typing.NoReturn:
        msg = "Method '__repr__' is not implemented for " f"{self.__class__.__name__}"
        raise NotImplementedError(
            msg,
        )

    def calc(
        self,
        tax_base: NumericalArray,
        right: bool,
    ) -> typing.NoReturn:
        msg = "Method 'calc' is not implemented for " f"{self.__class__.__name__}"
        raise NotImplementedError(
            msg,
        )

    def to_dict(self) -> typing.NoReturn:
        msg = f"Method 'to_dict' is not implemented for {self.__class__.__name__}"
        raise NotImplementedError(
            msg,
        )
