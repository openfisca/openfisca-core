from __future__ import annotations

import typing

import numpy

from openfisca_core import taxscales
from openfisca_core.taxscales import AmountTaxScaleLike

if typing.TYPE_CHECKING:
    NumericalArray = typing.Union[numpy.int_, numpy.float_]


class SingleAmountTaxScale(AmountTaxScaleLike):
    def calc(
        self,
        tax_base: NumericalArray,
        right: bool = False,
    ) -> numpy.float_:
        """
        Matches the input amount to a set of brackets and returns the single
        cell value that fits within that bracket.
        """
        guarded_thresholds = numpy.array([-numpy.inf] + self.thresholds + [numpy.inf])

        bracket_indices = numpy.digitize(
            tax_base,
            guarded_thresholds,
            right=right,
        )

        guarded_amounts = numpy.array([0] + self.amounts + [0])

        return guarded_amounts[bracket_indices - 1]

    def to_average(self) -> taxscales.LinearAverageRateTaxScale:
        """ Converts this scale to a LinearAverageRateTaxScale.
            Parameter keys change from ('threshold', 'amount') to ('threshold', 'rate').
        """
        average_tax_scale = taxscales.LinearAverageRateTaxScale(
            name = self.name,
            option = self.option,
            unit = self.unit,
            )
        

        for threshold, amount in zip(self.thresholds, self.amounts):
            try:
                average_tax_scale.add_bracket(threshold, amount/threshold)
            except ZeroDivisionError:
                average_tax_scale.add_bracket(threshold, 0)
            

        return average_tax_scale
