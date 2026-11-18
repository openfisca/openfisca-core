from __future__ import annotations

import bisect
import itertools
import typing

import numpy

from openfisca_core import scales

from .rate_scale_like import RateScaleLike

if typing.TYPE_CHECKING:
    NumericalArray = numpy.int32 | numpy.float32


class MarginalRateScale(RateScaleLike):
    def add_scale(self, scale: RateScaleLike) -> None:
        # So as not to have problems with empty scales
        if len(scale.thresholds) > 0:
            for threshold_low, threshold_high, rate in zip(
                scale.thresholds[:-1],
                scale.thresholds[1:],
                scale.rates,
            ):
                self.combine_bracket(rate, threshold_low, threshold_high)

            # To process the last threshold
            self.combine_bracket(
                scale.rates[-1],
                scale.thresholds[-1],
            )

    def calc(
        self,
        base: NumericalArray,
        factor: float = 1.0,
        round_base_decimals: int | None = None,
    ) -> numpy.float32:
        """Compute the tax amount for the given tax bases by applying a scale.

        :param ndarray base: Array of the tax bases.
        :param float factor: Factor to apply to the thresholds of the scale.
        :param int round_base_decimals: Decimals to keep when rounding
                                        thresholds.

        :returns: Float array with tax amount for the given tax bases.

        For instance:

        >>> scale = MarginalRateScale()
        >>> scale.add_bracket(0, 0)
        >>> scale.add_bracket(100, 0.1)
        >>> base = array([0, 150])
        >>> scale.calc(base)
        [0.0, 5.0]
        """
        base1 = numpy.tile(base, (len(self.thresholds), 1)).T
        factor = numpy.ones(len(base)) * factor

        # To avoid the creation of:
        #
        #   numpy.nan = 0 * numpy.inf
        #
        # We use:
        #
        #   numpy.finfo(float_).eps
        thresholds1 = numpy.outer(
            factor + numpy.finfo(numpy.float64).eps,
            numpy.array([*self.thresholds, numpy.inf]),
        )

        if round_base_decimals is not None:
            thresholds1 = numpy.round(thresholds1, round_base_decimals)

        a = numpy.maximum(
            numpy.minimum(base1, thresholds1[:, 1:]) - thresholds1[:, :-1],
            0,
        )

        if round_base_decimals is None:
            return numpy.dot(self.rates, a.T)

        r = numpy.tile(self.rates, (len(base), 1))
        b = numpy.round(a, round_base_decimals)
        return numpy.round(r * b, round_base_decimals).sum(axis=1)

    def combine_bracket(
        self,
        rate: float,
        threshold_low: int = 0,
        threshold_high: int | bool = False,
    ) -> None:
        # Insert threshold_low and threshold_high without modifying rates
        if threshold_low not in self.thresholds:
            index = bisect.bisect_right(self.thresholds, threshold_low) - 1
            self.add_bracket(threshold_low, self.rates[index])

        if threshold_high and threshold_high not in self.thresholds:
            index = bisect.bisect_right(self.thresholds, threshold_high) - 1
            self.add_bracket(threshold_high, self.rates[index])

        # Use add_bracket to add rates where they belongs
        i = self.thresholds.index(threshold_low)

        if threshold_high:
            j = self.thresholds.index(threshold_high) - 1

        else:
            j = len(self.thresholds) - 1

        while i <= j:
            self.add_bracket(self.thresholds[i], rate)
            i += 1

    def marginal_rates(
        self,
        base: NumericalArray,
        factor: float = 1.0,
        round_base_decimals: int | None = None,
    ) -> numpy.float32:
        """Compute the marginal tax rates relevant for the given tax bases.

        :param ndarray base: Array of the tax bases.
        :param float factor: Factor to apply to the thresholds of a tax scale.
        :param int round_base_decimals: Decimals to keep when rounding
                                        thresholds.

        :returns: Float array with relevant marginal tax rate for the given tax
                  bases.

        For instance:

        >>> scale = MarginalRateScale()
        >>> scale.add_bracket(0, 0)
        >>> scale.add_bracket(100, 0.1)
        >>> base = array([0, 150])
        >>> scale.marginal_rates(base)
        [0.0, 0.1]
        """
        bracket_indices = self.bracket_indices(
            base,
            factor,
            round_base_decimals,
        )

        return numpy.array(self.rates)[bracket_indices]

    def rate_from_bracket_indice(
        self,
        bracket_indice: numpy.int16,
    ) -> numpy.float32:
        """Compute the relevant tax rates for the given bracket indices.

        :param: ndarray bracket_indice: Array of the bracket indices.

        :returns: Floating array with relevant tax rates
                  for the given bracket indices.

        For instance:

        >>> import numpy
        >>> scale = MarginalRateScale()
        >>> scale.add_bracket(0, 0)
        >>> scale.add_bracket(200, 0.1)
        >>> scale.add_bracket(500, 0.25)
        >>> base = numpy.array([50, 1_000, 250])
        >>> bracket_indice = scale.bracket_indices(base)
        >>> scale.rate_from_bracket_indice(bracket_indice)
        array([0.  , 0.25, 0.1 ])
        """
        if bracket_indice.max() > len(self.rates) - 1:
            msg = (
                f"bracket_indice parameter ({bracket_indice}) "
                f"contains one or more bracket indice which is unavailable "
                f"inside current {self.__class__.__name__} :\n"
                f"{self}"
            )
            raise IndexError(
                msg,
            )

        return numpy.array(self.rates)[bracket_indice]

    def rate_from_base(
        self,
        base: NumericalArray,
    ) -> numpy.float32:
        """Compute the relevant tax rates for the given tax bases.

        :param: ndarray base: Array of the tax bases.

        :returns: Floating array with relevant tax rates
                  for the given tax bases.

        For instance:

        >>> import numpy
        >>> scale = MarginalRateScale()
        >>> scale.add_bracket(0, 0)
        >>> scale.add_bracket(200, 0.1)
        >>> scale.add_bracket(500, 0.25)
        >>> base = numpy.array([1_000, 50, 450])
        >>> scale.rate_from_base(base)
        array([0.25, 0.  , 0.1 ])
        """
        return self.rate_from_bracket_indice(self.bracket_indices(base))

    def inverse(self) -> MarginalRateScale:
        """Returns a new instance of MarginalRateScale.

        Invert a scale:

            Assume scale composed of bracket whose thresholds are expressed
            in terms of gross revenue.

            The inverse is another MarginalRateScale whose thresholds are
            expressed in terms of net revenue.

            If net = gross_revenue - scale.calc(gross_revenue)
            Then gross = scale.inverse().calc(net)
        """
        # Threshold of net revenue.
        net_threshold: int = 0

        # Threshold of gross revenue.
        threshold: int

        # The intercept of the segments of the different thresholds in a
        # representation of taxable revenue as a piecewise linear function
        # of gross revenue.
        theta: int

        # Actually 1 / (1 - global_rate)
        inverse = self.__class__(
            name=str(self.name) + "'",
            option=self.option,
            unit=self.unit,
        )

        for threshold, rate in zip(self.thresholds, self.rates):
            if threshold == 0:
                previous_rate = 0
                theta = 0

            # We calculate the taxable revenue threshold of the considered
            # bracket.
            net_threshold = (1 - previous_rate) * threshold + theta
            inverse.add_bracket(net_threshold, 1 / (1 - rate))
            theta = (rate - previous_rate) * threshold + theta
            previous_rate = rate

        return inverse

    def scale_scales(self, factor: float) -> MarginalRateScale:
        """Scale all the MarginalRateScales in the node."""
        scaled_scale = self.copy()
        return scaled_scale.multiply_thresholds(factor)

    def to_average(self) -> scales.AverageRateScale:
        average_scale = scales.AverageRateScale(
            name=self.name,
            option=self.option,
            unit=self.unit,
        )

        average_scale.add_bracket(0, 0)

        if self.thresholds:
            i = 0
            previous_threshold = self.thresholds[0]
            previous_rate = self.rates[0]

            for threshold, rate in itertools.islice(
                zip(self.thresholds, self.rates),
                1,
                None,
            ):
                i += previous_rate * (threshold - previous_threshold)
                average_scale.add_bracket(threshold, i / threshold)
                previous_threshold = threshold
                previous_rate = rate

            average_scale.add_bracket(float("Inf"), rate)

        return average_scale
