from __future__ import annotations

import typing

import numpy

from openfisca_core.taxscales import AmountTaxScaleLike


class SingleAmountTaxScale(AmountTaxScaleLike):

    def calc(
            self,
            tax_base: typing.Union[numpy.ndarray[int], numpy.ndarray[float]],
            right: bool = False,
            interpolate: bool = False,
            interp_right: typing.Union[numpy.ndarray[int], numpy.ndarray[float], None] = None,
            interp_left: typing.Union[numpy.ndarray[int], numpy.ndarray[float], None] = None,
            ) -> numpy.ndarray[float]:
        """
        Matches the input amount to a set of brackets and returns the single cell value
        that fits within that bracket.

        :arguments:
        - `interpolate` (bool): if True, returns the linear interpolated value
                                between the nearest two thresholds.
        - `interp_right` (int, float): value returned in `tax_base` is greater than the highest threshold value
        - `interp_left` (int, float): value returned in `tax_base` is less than the lowest threshold value

        """
        if interpolate:
            thresholds = self.thresholds
            amounts = self.amounts
            result = numpy.interp(tax_base, thresholds, amounts, left=interp_left, right=interp_right)
            return result

        else:
            guarded_thresholds = numpy.array([-numpy.inf] + self.thresholds + [numpy.inf])
            bracket_indices = numpy.digitize(tax_base, guarded_thresholds, right = right)
            guarded_amounts = numpy.array([0] + self.amounts + [0])
            return guarded_amounts[bracket_indices - 1]
