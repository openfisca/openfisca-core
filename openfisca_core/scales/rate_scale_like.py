from __future__ import annotations

import abc
import bisect
import os
import typing

import numpy

from openfisca_core import tools
from openfisca_core.errors import EmptyArgumentError

from .scale_like import ScaleLike

if typing.TYPE_CHECKING:
    NumericalArray = numpy.int32 | numpy.float32


class RateScaleLike(ScaleLike, abc.ABC):
    """Base class for various types of rate-based tax scales: marginal rate,
    average rate...
    """

    rates: list

    def __init__(
        self,
        name: str | None = None,
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
                    for (threshold, rate) in zip(self.thresholds, self.rates)
                ],
            ),
        )

    def add_bracket(
        self,
        threshold: float,
        rate: float,
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
        new_name: str | None = None,
    ) -> RateScaleLike:
        if inplace:
            assert new_name is None

            for i, rate in enumerate(self.rates):
                self.rates[i] = rate * factor

            return self

        new_scale = self.__class__(
            new_name or self.name,
            option=self.option,
            unit=self.unit,
        )

        for threshold, rate in zip(self.thresholds, self.rates):
            new_scale.thresholds.append(threshold)
            new_scale.rates.append(rate * factor)

        return new_scale

    def multiply_thresholds(
        self,
        factor: float,
        decimals: int | None = None,
        inplace: bool = True,
        new_name: str | None = None,
    ) -> RateScaleLike:
        if inplace:
            assert new_name is None

            for i, threshold in enumerate(self.thresholds):
                if decimals is not None:
                    self.thresholds[i] = numpy.around(
                        threshold * factor,
                        decimals=decimals,
                    )

                else:
                    self.thresholds[i] = threshold * factor

            return self

        new_scale = self.__class__(
            new_name or self.name,
            option=self.option,
            unit=self.unit,
        )

        for threshold, rate in zip(self.thresholds, self.rates):
            if decimals is not None:
                new_scale.thresholds.append(
                    numpy.around(threshold * factor, decimals=decimals),
                )
            else:
                new_scale.thresholds.append(threshold * factor)

            new_scale.rates.append(rate)

        return new_scale

    def bracket_indices(
        self,
        base: NumericalArray,
        factor: float = 1.0,
        round_decimals: int | None = None,
    ) -> numpy.int32:
        """Compute the relevant bracket indices for the given tax bases.

        :param ndarray base: Array of the tax bases.
        :param float factor: Factor to apply to the thresholds.
        :param int round_decimals: Decimals to keep when rounding thresholds.

        :returns: Integer array with relevant bracket indices for the given tax
                  bases.

        For instance:

        >>> scale = AverageRateScale()
        >>> scale.add_bracket(0, 0)
        >>> scale.add_bracket(100, 0.1)
        >>> base = array([0, 150])
        >>> scale.bracket_indices(base)
        [0, 1]
        """
        if not numpy.size(numpy.array(self.thresholds)):
            raise EmptyArgumentError(
                self.__class__.__name__,
                "bracket_indices",
                "self.thresholds",
                self.thresholds,
            )

        if not numpy.size(numpy.asarray(base)):
            raise EmptyArgumentError(
                self.__class__.__name__,
                "bracket_indices",
                "base",
                base,
            )

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
            +factor + numpy.finfo(numpy.float64).eps,
            numpy.array(self.thresholds),
        )

        if round_decimals is not None:
            thresholds1 = numpy.round(thresholds1, round_decimals)

        return (base1 - thresholds1 >= 0).sum(axis=1) - 1

    def threshold_from_base(
        self,
        base: NumericalArray,
    ) -> NumericalArray:
        """Compute the relevant thresholds for the given tax bases.

        :param: ndarray base: Array of the tax bases.

        :returns: Floating array with relevant thresholds
                  for the given tax bases.

        For instance:

        >>> import numpy
        >>> from openfisca_core import scales
        >>> scale = scales.MarginalRateScale()
        >>> scale.add_bracket(0, 0)
        >>> scale.add_bracket(200, 0.1)
        >>> scale.add_bracket(500, 0.25)
        >>> base = numpy.array([450, 1_150, 10])
        >>> scale.threshold_from_base(base)
        array([200, 500,   0])
        """
        return numpy.array(self.thresholds)[self.bracket_indices(base)]

    def to_dict(self) -> dict:
        return {
            str(threshold): self.rates[index]
            for index, threshold in enumerate(self.thresholds)
        }
