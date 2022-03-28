from __future__ import annotations

import abc
import bisect
import os
import typing

import numpy

from openfisca_core import tools
from openfisca_core.errors import EmptyArgumentError
from openfisca_core.taxscales import TaxScaleLike

if typing.TYPE_CHECKING:
    NumericalArray = typing.Union[numpy.int_, numpy.float_]


class RateTaxScaleLike(TaxScaleLike, abc.ABC):
    """
    Base class for various types of rate-based tax scales: marginal rate,
    linear average rate...
    """

    rates: typing.List

    def __init__(
            self,
            name: typing.Optional[str] = None,
            option: typing.Any = None,
            unit: typing.Any = None,
            ) -> None:
        super().__init__(name, option, unit)
        self.rates = []

    def __repr__(self) -> str:
        return tools.indent(
            os.linesep.join(
                [
                    f"- threshold: {threshold}{os.linesep}  rate: {rate}"
                    for (threshold, rate)
                    in zip(self.thresholds, self.rates)
                    ]
                )
            )

    def add_bracket(
            self,
            threshold: typing.Union[int, float],
            rate: typing.Union[int, float],
            ) -> None:
        if threshold in self.thresholds:
            i = self.thresholds.index(threshold)
            self.rates[i] += rate

        else:
            i = bisect.bisect_left(self.thresholds, threshold)
            self.thresholds.insert(i, threshold)
            self.rates.insert(i, rate)

    def multiply_rates(
            self,
            factor: float,
            inplace: bool = True,
            new_name: typing.Optional[str] = None,
            ) -> RateTaxScaleLike:
        if inplace:
            assert new_name is None

            for i, rate in enumerate(self.rates):
                self.rates[i] = rate * factor

            return self

        new_tax_scale = self.__class__(
            new_name or self.name,
            option = self.option,
            unit = self.unit,
            )

        for threshold, rate in zip(self.thresholds, self.rates):
            new_tax_scale.thresholds.append(threshold)
            new_tax_scale.rates.append(rate * factor)

        return new_tax_scale

    def multiply_thresholds(
            self,
            factor: float,
            decimals: typing.Optional[int] = None,
            inplace: bool = True,
            new_name: typing.Optional[str] = None,
            ) -> RateTaxScaleLike:
        if inplace:
            assert new_name is None

            for i, threshold in enumerate(self.thresholds):
                if decimals is not None:
                    self.thresholds[i] = numpy.around(
                        threshold * factor,
                        decimals = decimals,
                        )

                else:
                    self.thresholds[i] = threshold * factor

            return self

        new_tax_scale = self.__class__(
            new_name or self.name,
            option = self.option,
            unit = self.unit,
            )

        for threshold, rate in zip(self.thresholds, self.rates):
            if decimals is not None:
                new_tax_scale.thresholds.append(
                    numpy.around(threshold * factor, decimals = decimals),
                    )
            else:
                new_tax_scale.thresholds.append(threshold * factor)

            new_tax_scale.rates.append(rate)

        return new_tax_scale

    def bracket_indices(
            self,
            tax_base: NumericalArray,
            factor: float = 1.0,
            round_decimals: typing.Optional[int] = None,
            ) -> numpy.int_:
        """
        Compute the relevant bracket indices for the given tax bases.

        :param ndarray tax_base: Array of the tax bases.
        :param float factor: Factor to apply to the thresholds.
        :param int round_decimals: Decimals to keep when rounding thresholds.

        :returns: Integer array with relevant bracket indices for the given tax
                  bases.

        For instance:

        >>> tax_scale = LinearAverageRateTaxScale()
        >>> tax_scale.add_bracket(0, 0)
        >>> tax_scale.add_bracket(100, 0.1)
        >>> tax_base = array([0, 150])
        >>> tax_scale.bracket_indices(tax_base)
        [0, 1]
        """

        if not numpy.size(numpy.array(self.thresholds)):
            raise EmptyArgumentError(
                self.__class__.__name__,
                "bracket_indices",
                "self.thresholds",
                self.thresholds,
                )

        if not numpy.size(numpy.asarray(tax_base)):
            raise EmptyArgumentError(
                self.__class__.__name__,
                "bracket_indices",
                "tax_base",
                tax_base,
                )

        base1 = numpy.tile(tax_base, (len(self.thresholds), 1)).T
        factor = numpy.ones(len(tax_base)) * factor

        # To avoid the creation of:
        #
        #   numpy.nan = 0 * numpy.inf
        #
        # We use:
        #
        #   numpy.finfo(float_).eps
        thresholds1 = numpy.outer(
            + factor
            + numpy.finfo(numpy.float_).eps, numpy.array(self.thresholds)
            )

        if round_decimals is not None:
            thresholds1 = numpy.round_(thresholds1, round_decimals)

        return (base1 - thresholds1 >= 0).sum(axis = 1) - 1

    def threshold_from_tax_base(
            self,
            tax_base: NumericalArray,
            ) -> NumericalArray:
        """
        Compute the relevant thresholds for the given tax bases.

        :param: ndarray tax_base: Array of the tax bases.

        :returns: Floating array with relevant thresholds
                  for the given tax bases.

        For instance:

        >>> import numpy
        >>> from openfisca_core import taxscales
        >>> tax_scale = taxscales.MarginalRateTaxScale()
        >>> tax_scale.add_bracket(0, 0)
        >>> tax_scale.add_bracket(200, 0.1)
        >>> tax_scale.add_bracket(500, 0.25)
        >>> tax_base = numpy.array([450, 1_150, 10])
        >>> tax_scale.threshold_from_tax_base(tax_base)
        array([200, 500,   0])
        """

        return numpy.array(self.thresholds)[self.bracket_indices(tax_base)]

    def to_dict(self) -> dict:
        return {
            str(threshold): self.rates[index]
            for index, threshold
            in enumerate(self.thresholds)
            }
