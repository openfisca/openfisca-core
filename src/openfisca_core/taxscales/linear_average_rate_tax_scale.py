from __future__ import annotations

import logging
import typing

import numpy

from openfisca_core import taxscales
from openfisca_core.taxscales import RateTaxScaleLike

log = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    NumericalArray = typing.Union[numpy.int_, numpy.float_]


class LinearAverageRateTaxScale(RateTaxScaleLike):

    def calc(
            self,
            tax_base: NumericalArray,
            right: bool = False,
            ) -> numpy.float_:
        if len(self.rates) == 1:
            return tax_base * self.rates[0]

        tiled_base = numpy.tile(tax_base, (len(self.thresholds) - 1, 1)).T
        tiled_thresholds = numpy.tile(self.thresholds, (len(tax_base), 1))

        bracket_dummy = (tiled_base >= tiled_thresholds[:, :-1]) * (
            + tiled_base
            < tiled_thresholds[:, 1:]
            )

        rates_array = numpy.array(self.rates)
        thresholds_array = numpy.array(self.thresholds)

        rate_slope = (rates_array[1:] - rates_array[:-1]) / (
            + thresholds_array[1:]
            - thresholds_array[:-1]
            )

        average_rate_slope = numpy.dot(bracket_dummy, rate_slope.T)

        bracket_average_start_rate = numpy.dot(bracket_dummy, rates_array[:-1])
        bracket_threshold = numpy.dot(bracket_dummy, thresholds_array[:-1])

        log.info(f"bracket_average_start_rate :  {bracket_average_start_rate}")
        log.info(f"average_rate_slope:  {average_rate_slope}")

        return tax_base * (
            + bracket_average_start_rate
            + (tax_base - bracket_threshold)
            * average_rate_slope
            )

    def to_marginal(self) -> taxscales.MarginalRateTaxScale:
        marginal_tax_scale = taxscales.MarginalRateTaxScale(
            name = self.name,
            option = self.option,
            unit = self.unit,
            )

        previous_i = 0
        previous_threshold = 0

        for threshold, rate in zip(self.thresholds[1:], self.rates[1:]):
            if threshold != float("Inf"):
                i = rate * threshold
                marginal_tax_scale.add_bracket(
                    previous_threshold,
                    (i - previous_i) / (threshold - previous_threshold),
                    )
                previous_i = i
                previous_threshold = threshold

        marginal_tax_scale.add_bracket(previous_threshold, rate)

        return marginal_tax_scale
