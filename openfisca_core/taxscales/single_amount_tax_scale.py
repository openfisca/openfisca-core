from __future__ import annotations

import typing

import numpy

from openfisca_core.taxscales import AmountTaxScaleLike


class SingleAmountTaxScale(AmountTaxScaleLike):

    def calc(
            self,
            tax_base: typing.Union[numpy.ndarray[int], numpy.ndarray[float]],
            right: bool = False,
            ) -> numpy.ndarray[float]:
        """
        Matches the input amount to a set of brackets and returns the single cell value
        that fits within that bracket.
        """
        guarded_thresholds = numpy.array([-numpy.inf] + self.thresholds + [numpy.inf])
        bracket_indices = numpy.digitize(tax_base, guarded_thresholds, right = right)
        guarded_amounts = numpy.array([0] + self.amounts + [0])
        return guarded_amounts[bracket_indices - 1]
