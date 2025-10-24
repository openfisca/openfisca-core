from __future__ import annotations

import typing

import numpy

from .amount_tax_scale_like import AmountTaxScaleLike

if typing.TYPE_CHECKING:
    NumericalArray = typing.Union[numpy.int32, numpy.float32]


class MarginalAmountTaxScale(AmountTaxScaleLike):
    def calc(
        self,
        tax_base: NumericalArray,
        right: bool = False,
    ) -> numpy.float32:
        """Matches the input amount to a set of brackets and returns the sum of
        cell values from the lowest bracket to the one containing the input.
        """
        base1 = numpy.tile(tax_base, (len(self.thresholds), 1)).T

        thresholds1 = numpy.tile(
            numpy.hstack((self.thresholds, numpy.inf)),
            (len(tax_base), 1),
        )

        a = numpy.maximum(
            numpy.minimum(base1, thresholds1[:, 1:]) - thresholds1[:, :-1],
            0,
        )

        return numpy.dot(self.amounts, a.T > 0)
