from __future__ import annotations

import typing

import numpy

from .amount_scale_like import AmountScaleLike

if typing.TYPE_CHECKING:
    NumericalArray = numpy.int32 | numpy.float32


class MarginalAmountScale(AmountScaleLike):
    def calc(
        self,
        base: NumericalArray,
        right: bool = False,
    ) -> numpy.float32:
        """Matches the input amount to a set of brackets and returns the sum of
        cell values from the lowest bracket to the one containing the input.
        """
        base1 = numpy.tile(base, (len(self.thresholds), 1)).T

        thresholds1 = numpy.tile(
            numpy.hstack((self.thresholds, numpy.inf)),
            (len(base), 1),
        )

        a = numpy.maximum(
            numpy.minimum(base1, thresholds1[:, 1:]) - thresholds1[:, :-1],
            0,
        )

        return numpy.dot(self.amounts, a.T > 0)
