from __future__ import annotations

import logging
import typing

import numpy

from openfisca_core import scales

from .rate_scale_like import RateScaleLike

log = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    NumericalArray = numpy.int32 | numpy.float32


class AverageRateScale(RateScaleLike):
    def calc(
        self,
        base: NumericalArray,
        right: bool = False,
    ) -> numpy.float32:
        if len(self.rates) == 1:
            return base * self.rates[0]

        tiled_base = numpy.tile(base, (len(self.thresholds) - 1, 1)).T
        tiled_thresholds = numpy.tile(self.thresholds, (len(base), 1))

        bracket_dummy = (tiled_base >= tiled_thresholds[:, :-1]) * (
            +tiled_base < tiled_thresholds[:, 1:]
        )

        rates_array = numpy.array(self.rates)
        thresholds_array = numpy.array(self.thresholds)

        rate_slope = (rates_array[1:] - rates_array[:-1]) / (
            +thresholds_array[1:] - thresholds_array[:-1]
        )

        average_rate_slope = numpy.dot(bracket_dummy, rate_slope.T)

        bracket_average_start_rate = numpy.dot(bracket_dummy, rates_array[:-1])
        bracket_threshold = numpy.dot(bracket_dummy, thresholds_array[:-1])

        log.info(f"bracket_average_start_rate :  {bracket_average_start_rate}")
        log.info(f"average_rate_slope:  {average_rate_slope}")

        return base * (
            +bracket_average_start_rate
            + (base - bracket_threshold) * average_rate_slope
        )

    def to_marginal(self) -> scales.MarginalRateScale:
        marginal_scale = scales.MarginalRateScale(
            name=self.name,
            option=self.option,
            unit=self.unit,
        )

        previous_i = 0
        previous_threshold = 0

        for threshold, rate in zip(self.thresholds[1:], self.rates[1:]):
            if threshold != float("Inf"):
                i = rate * threshold
                marginal_scale.add_bracket(
                    previous_threshold,
                    (i - previous_i) / (threshold - previous_threshold),
                )
                previous_i = i
                previous_threshold = threshold

        marginal_scale.add_bracket(previous_threshold, rate)

        return marginal_scale
