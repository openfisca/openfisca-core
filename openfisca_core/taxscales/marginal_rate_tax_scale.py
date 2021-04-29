from __future__ import annotations

import bisect
import itertools
import typing

import numpy

from openfisca_core import taxscales
from openfisca_core.taxscales import RateTaxScaleLike


class MarginalRateTaxScale(RateTaxScaleLike):

    def add_tax_scale(self, tax_scale: RateTaxScaleLike) -> None:
        # Pour ne pas avoir de problèmes avec les barèmes vides
        if (len(tax_scale.thresholds) > 0):
            for threshold_low, threshold_high, rate in zip(
                    tax_scale.thresholds[:-1],
                    tax_scale.thresholds[1:],
                    tax_scale.rates,
                    ):
                self.combine_bracket(rate, threshold_low, threshold_high)

            # Pour traiter le dernier threshold
            self.combine_bracket(
                tax_scale.rates[-1],
                tax_scale.thresholds[-1],
                )

    def calc(
            self,
            tax_base: typing.Union[numpy.ndarray[int], numpy.ndarray[float]],
            factor: float = 1.0,
            round_base_decimals: typing.Optional[int] = None,
            ) -> numpy.ndarray[float]:
        """
        Compute the tax amount for the given tax bases by applying the taxscale.

        :param ndarray tax_base: Array of the tax bases.
        :param float factor: Factor to apply to the thresholds of the tax scale.
        :param int round_base_decimals: Decimals to keep when rounding thresholds.

        :returns: Float array with tax amount for the given tax bases.

        For instance:

        >>> tax_scale = MarginalRateTaxScale()
        >>> tax_scale.add_bracket(0, 0)
        >>> tax_scale.add_bracket(100, 0.1)
        >>> tax_base = array([0, 150])
        >>> tax_scale.calc(tax_base)
        [0.0, 5.0]
        """

        base1 = numpy.tile(tax_base, (len(self.thresholds), 1)).T
        factor = numpy.ones(len(tax_base)) * factor

        # finfo(float_).eps is used to avoid nan = 0 * inf creation
        thresholds1 = numpy.outer(factor + numpy.finfo(numpy.float_).eps, numpy.array(self.thresholds + [numpy.inf]))

        if round_base_decimals is not None:
            thresholds1 = numpy.round_(thresholds1, round_base_decimals)

        a = numpy.maximum(numpy.minimum(base1, thresholds1[:, 1:]) - thresholds1[:, :-1], 0)

        if round_base_decimals is None:
            return numpy.dot(self.rates, a.T)
        else:
            r = numpy.tile(self.rates, (len(tax_base), 1))
            b = numpy.round_(a, round_base_decimals)
            return numpy.round_(r * b, round_base_decimals).sum(axis = 1)

    def combine_bracket(
            self,
            rate: typing.Union[int, float],
            threshold_low: int = 0,
            threshold_high: typing.Union[int, bool] = False,
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
            tax_base: typing.Union[numpy.ndarray[int], numpy.ndarray[float]],
            factor: float = 1.0,
            round_base_decimals: typing.Optional[int] = None,
            ) -> numpy.ndarray[float]:
        """
        Compute the marginal tax rates relevant for the given tax bases.

        :param ndarray tax_base: Array of the tax bases.
        :param float factor: Factor to apply to the thresholds of the tax scale.
        :param int round_base_decimals: Decimals to keep when rounding thresholds.

        :returns: Float array with relevant marginal tax rate for the given tax bases.

        For instance:

        >>> tax_scale = MarginalRateTaxScale()
        >>> tax_scale.add_bracket(0, 0)
        >>> tax_scale.add_bracket(100, 0.1)
        >>> tax_base = array([0, 150])
        >>> tax_scale.marginal_rates(tax_base)
        [0.0, 0.1]
        """
        bracket_indices = self.bracket_indices(
            tax_base,
            factor,
            round_base_decimals,
            )

        return numpy.array(self.rates)[bracket_indices]

    def inverse(self) -> MarginalRateTaxScale:
        """
        Returns a new instance of MarginalRateTaxScale.

        Invert a taxscale:

            Assume tax_scale composed of bracket which thresholds are expressed in term
            of brut revenue.

            The inverse is another MarginalTaxSclae which thresholds are expressed in
            terms of net revenue.

            IF net = revbrut - tax_scale.calc(revbrut)
            THEN brut = tax_scale.inverse().calc(net)
        """
        # Threshold of net revenue.
        net_threshold: int = 0

        # Threshold of brut revenue.
        threshold: int

        # Ordonnée à l'origine des segments des différents seuils dans une
        # représentation du revenu imposable comme fonction linéaire par morceaux du
        # revenu brut.
        theta: int

        # Actually 1 / (1- global_rate)
        inverse = self.__class__(
            name = self.name + "'",
            option = self.option,
            unit = self.unit,
            )

        for threshold, rate in zip(self.thresholds, self.rates):
            if threshold == 0:
                previous_rate = 0
                theta = 0

            # On calcule le seuil de revenu imposable de la tranche considérée.
            net_threshold = (1 - previous_rate) * threshold + theta
            inverse.add_bracket(net_threshold, 1 / (1 - rate))
            theta = (rate - previous_rate) * threshold + theta
            previous_rate = rate

        return inverse

    def scale_tax_scales(self, factor: float) -> MarginalRateTaxScale:
        """Scale all the MarginalRateTaxScales in the node."""
        scaled_tax_scale = self.copy()
        return scaled_tax_scale.multiply_thresholds(factor)

    def to_average(self) -> taxscales.LinearAverageRateTaxScale:
        average_tax_scale = taxscales.LinearAverageRateTaxScale(
            name = self.name,
            option = self.option,
            unit = self.unit,
            )

        average_tax_scale.add_bracket(0, 0)

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
                average_tax_scale.add_bracket(threshold, i / threshold)
                previous_threshold = threshold
                previous_rate = rate

            average_tax_scale.add_bracket(float("Inf"), rate)

        return average_tax_scale
