from __future__ import annotations

import abc
import bisect
import copy
import itertools
import logging
import os
import traceback
import warnings
from typing import Any, List, NoReturn, Optional, Union

from numpy import (
    around,
    array,
    asarray,
    digitize,
    dot,
    finfo,
    float as float_,
    hstack,
    inf,
    maximum as max_,
    minimum as min_,
    ndarray,
    ones,
    outer,
    round as round_,
    size,
    tile,
    )

from openfisca_core import commons
from openfisca_core import tools

log = logging.getLogger(__name__)


class EmptyArgumentError(IndexError):
    """Exception raised when a method is called with an empty argument."""

    message: str

    def __init__(
            self,
            class_name: str,
            method_name: str,
            arg_name: str,
            arg_value: Union[List, ndarray]
            ) -> None:
        message = [
            f"'{class_name}.{method_name}' can't be run with an empty '{arg_name}':\n",
            f">>> {arg_name}",
            f"{arg_value}\n",
            "Here are some hints to help you get this working:\n",
            f"- Check that '{class_name}' isn't empty (see '{class_name}.add_bracket')",
            f"- Check that '{arg_name}' is being properly assigned "
            f"('{arg_name}' should be a non empty '{type(arg_value).__name__}')\n",
            "For further support, please do not hesitate to:\n",
            "- Take a look at the official documentation https://openfisca.org/doc",
            "- Open an issue on https://github.com/openfisca/openfisca-core/issues/new",
            "- Mention us via https://twitter.com/openfisca",
            "- Drop us a line to contact@openfisca.org\n",
            "😃",
            ]
        stacktrace = os.linesep.join(traceback.format_stack())
        self.message = os.linesep.join([f"  {line}" for line in message])
        self.message = os.linesep.join([stacktrace, self.message])
        super().__init__(self.message)


class TaxScaleLike(abc.ABC):
    """
    Base class for various types of tax scales: amount-based tax scales, rate-based
    tax scales...
    """

    name: str
    option: None
    unit: None
    thresholds: List

    @abc.abstractmethod
    def __init__(self, name: Optional[str] = None, option = None, unit = None) -> None:
        self.name = name or "Untitled TaxScale"
        self.option = option
        self.unit = unit
        self.thresholds = []

    def __eq__(self, _other: object) -> NoReturn:
        raise NotImplementedError(
            "Method '__eq__' is not implemented for "
            f"{self.__class__.__name__}",
            )

    def __ne__(self, _other: object) -> NoReturn:
        raise NotImplementedError(
            "Method '__ne__' is not implemented for "
            f"{self.__class__.__name__}",
            )

    @abc.abstractmethod
    def __repr__(self) -> str:
        ...

    @abc.abstractmethod
    def calc(
            self,
            tax_base: Union[ndarray[int], ndarray[float]],
            right: bool,
            ) -> ndarray[float]:
        ...

    @abc.abstractmethod
    def to_dict(self) -> dict:
        ...

    def copy(self) -> Any:
        new = commons.empty_clone(self)
        new.__dict__ = copy.deepcopy(self.__dict__)
        return new


class AbstractTaxScale(TaxScaleLike):
    """
    Base class for various types of tax scales: amount-based tax scales, rate-based
    tax scales...
    """

    def __init__(self, name: Optional[str] = None, option = None, unit = None) -> None:
        message = [
            "The 'AbstractTaxScale' class has been deprecated since version 34.7.0,",
            "and will be removed in the future.",
            ]
        warnings.warn(" ".join(message), DeprecationWarning)
        super(AbstractTaxScale, self).__init__(name, option, unit)

    def __repr__(self) -> NoReturn:
        raise NotImplementedError(
            "Method '__repr__' is not implemented for "
            f"{self.__class__.__name__}",
            )

    def calc(
            self,
            tax_base: Union[ndarray[int], ndarray[float]],
            right: bool,
            ) -> NoReturn:
        raise NotImplementedError(
            "Method 'calc' is not implemented for "
            f"{self.__class__.__name__}",
            )

    def to_dict(self) -> NoReturn:
        raise NotImplementedError(
            f"Method 'to_dict' is not implemented for "
            f"{self.__class__.__name__}",
            )


class AmountTaxScaleLike(TaxScaleLike, abc.ABC):
    """
    Base class for various types of amount-based tax scales: single amount, marginal
    amount...
    """

    amounts: List

    def __init__(self, name: Optional[str] = None, option = None, unit = None) -> None:
        super(AmountTaxScaleLike, self).__init__(name, option, unit)
        self.amounts = []

    def __repr__(self) -> str:
        return tools.indent(
            os.linesep.join(
                [
                    f"- threshold: {threshold}{os.linesep}  amount: {amount}"
                    for (threshold, amount) in zip(self.thresholds, self.amounts)
                    ]
                )
            )

    def add_bracket(
            self,
            threshold: int,
            amount: Union[int, float],
            ) -> None:
        if threshold in self.thresholds:
            i = self.thresholds.index(threshold)
            self.amounts[i] += amount
        else:
            i = bisect.bisect_left(self.thresholds, threshold)
            self.thresholds.insert(i, threshold)
            self.amounts.insert(i, amount)

    def to_dict(self) -> dict:
        return {
            str(threshold): self.amounts[index]
            for index, threshold in enumerate(self.thresholds)
            }


class RateTaxScaleLike(TaxScaleLike, abc.ABC):
    """
    Base class for various types of rate-based tax scales: marginal rate, linear
    average rate...
    """

    rates: List

    def __init__(self, name: Optional[str] = None, option = None, unit = None) -> None:
        super(RateTaxScaleLike, self).__init__(name, option, unit)
        self.rates = []

    def __repr__(self) -> str:
        return tools.indent(
            os.linesep.join(
                [
                    f"- threshold: {threshold}{os.linesep}  rate: {rate}"
                    for (threshold, rate) in zip(self.thresholds, self.rates)
                    ]
                )
            )

    def add_bracket(
            self,
            threshold: Union[int, float],
            rate: Union[int, float],
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
            new_name: Optional[str] = None,
            ) -> "RateTaxScaleLike":
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
            decimals: Optional[int] = None,
            inplace: bool = True,
            new_name: Optional[str] = None,
            ) -> "RateTaxScaleLike":
        if inplace:
            assert new_name is None

            for i, threshold in enumerate(self.thresholds):
                if decimals is not None:
                    self.thresholds[i] = around(threshold * factor, decimals = decimals)
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
                    around(threshold * factor, decimals = decimals),
                    )
            else:
                new_tax_scale.thresholds.append(threshold * factor)

            new_tax_scale.rates.append(rate)

        return new_tax_scale

    def bracket_indices(
            self,
            tax_base: Union[ndarray[int], ndarray[float]],
            factor: float = 1.0,
            round_decimals: Optional[int] = None,
            ) -> ndarray[int]:
        """
        Compute the relevant bracket indices for the given tax bases.

        :param ndarray tax_base: Array of the tax bases.
        :param float factor: Factor to apply to the thresholds of the tax scales.
        :param int round_decimals: Decimals to keep when rounding thresholds.

        :returns: Int array with relevant bracket indices for the given tax bases.

        For instance:

        >>> tax_scale = LinearAverageRateTaxScale()
        >>> tax_scale.add_bracket(0, 0)
        >>> tax_scale.add_bracket(100, 0.1)
        >>> tax_base = array([0, 150])
        >>> tax_scale.bracket_indices(tax_base)
        [0, 1]
        """

        if not size(array(self.thresholds)):
            raise EmptyArgumentError(
                self.__class__.__name__,
                "bracket_indices",
                "self.thresholds",
                self.thresholds,
                )

        if not size(asarray(tax_base)):
            raise EmptyArgumentError(
                self.__class__.__name__,
                "bracket_indices",
                "tax_base",
                tax_base,
                )

        base1 = tile(tax_base, (len(self.thresholds), 1)).T
        factor = ones(len(tax_base)) * factor

        # finfo(float_).eps is used to avoid nan = 0 * inf creation
        thresholds1 = outer(factor + finfo(float_).eps, array(self.thresholds))

        if round_decimals is not None:
            thresholds1 = round_(thresholds1, round_decimals)

        return (base1 - thresholds1 >= 0).sum(axis = 1) - 1

    def to_dict(self) -> dict:
        return {
            str(threshold): self.rates[index]
            for index, threshold in enumerate(self.thresholds)
            }


class AbstractRateTaxScale(RateTaxScaleLike):
    """
    Base class for various types of rate-based tax scales: marginal rate, linear
    average rate...
    """

    def __init__(self, name: Optional[str] = None, option = None, unit = None) -> None:
        message = [
            "The 'AbstractRateTaxScale' class has been deprecated since version",
            "34.7.0, and will be removed in the future.",
            ]
        warnings.warn(" ".join(message), DeprecationWarning)
        super(AbstractRateTaxScale, self).__init__(name, option, unit)

    def calc(
            self,
            tax_base: Union[ndarray[int], ndarray[float]],
            right: bool,
            ) -> NoReturn:
        raise NotImplementedError(
            "Method 'calc' is not implemented for "
            f"{self.__class__.__name__}",
            )


class SingleAmountTaxScale(AmountTaxScaleLike):

    def calc(
            self,
            tax_base: Union[ndarray[int], ndarray[float]],
            right: bool = False,
            ) -> ndarray[float]:
        """
        Matches the input amount to a set of brackets and returns the single cell value
        that fits within that bracket.
        """
        guarded_thresholds = array([-inf] + self.thresholds + [inf])
        bracket_indices = digitize(tax_base, guarded_thresholds, right = right)
        guarded_amounts = array([0] + self.amounts + [0])
        return guarded_amounts[bracket_indices - 1]


class MarginalAmountTaxScale(AmountTaxScaleLike):

    def calc(
            self,
            tax_base: Union[ndarray[int], ndarray[float]],
            right: bool = False,
            ) -> ndarray[float]:
        """
        Matches the input amount to a set of brackets and returns the sum of cell
        values from the lowest bracket to the one containing the input.
        """
        base1 = tile(tax_base, (len(self.thresholds), 1)).T
        thresholds1 = tile(hstack((self.thresholds, inf)), (len(tax_base), 1))
        a = max_(min_(base1, thresholds1[:, 1:]) - thresholds1[:, :-1], 0)
        return dot(self.amounts, a.T > 0)


class LinearAverageRateTaxScale(RateTaxScaleLike):

    def calc(
            self,
            tax_base: Union[ndarray[int], ndarray[float]],
            right: bool = False,
            ) -> ndarray[float]:
        if len(self.rates) == 1:
            return tax_base * self.rates[0]

        tiled_base = tile(tax_base, (len(self.thresholds) - 1, 1)).T
        tiled_thresholds = tile(self.thresholds, (len(tax_base), 1))

        bracket_dummy = (tiled_base >= tiled_thresholds[:, :-1]) * (
            + tiled_base
            < tiled_thresholds[:, 1:]
            )

        rates_array = array(self.rates)
        thresholds_array = array(self.thresholds)

        rate_slope = (rates_array[1:] - rates_array[:-1]) / (
            + thresholds_array[1:]
            - thresholds_array[:-1]
            )

        average_rate_slope = dot(bracket_dummy, rate_slope.T)

        bracket_average_start_rate = dot(bracket_dummy, rates_array[:-1])
        bracket_threshold = dot(bracket_dummy, thresholds_array[:-1])

        log.info(f"bracket_average_start_rate :  {bracket_average_start_rate}")
        log.info(f"average_rate_slope:  {average_rate_slope}")

        return tax_base * (
            + bracket_average_start_rate
            + (tax_base - bracket_threshold)
            * average_rate_slope
            )

    def to_marginal(self) -> "MarginalRateTaxScale":
        marginal_tax_scale = MarginalRateTaxScale(
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
            tax_base: Union[ndarray[int], ndarray[float]],
            factor: float = 1.0,
            round_base_decimals: Optional[int] = None,
            ) -> ndarray[float]:
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

        base1 = tile(tax_base, (len(self.thresholds), 1)).T
        factor = ones(len(tax_base)) * factor

        # finfo(float_).eps is used to avoid nan = 0 * inf creation
        thresholds1 = outer(factor + finfo(float_).eps, array(self.thresholds + [inf]))

        if round_base_decimals is not None:
            thresholds1 = round_(thresholds1, round_base_decimals)

        a = max_(min_(base1, thresholds1[:, 1:]) - thresholds1[:, :-1], 0)

        if round_base_decimals is None:
            return dot(self.rates, a.T)
        else:
            r = tile(self.rates, (len(tax_base), 1))
            b = round_(a, round_base_decimals)
            return round_(r * b, round_base_decimals).sum(axis = 1)

    def combine_bracket(
            self,
            rate: Union[int, float],
            threshold_low: int = 0,
            threshold_high: Union[int, bool] = False,
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
            tax_base: Union[ndarray[int], ndarray[float]],
            factor: float = 1.0,
            round_base_decimals: Optional[int] = None,
            ) -> ndarray[float]:
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

        return array(self.rates)[bracket_indices]

    def inverse(self) -> "MarginalRateTaxScale":
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

    def scale_tax_scales(self, factor: float) -> "MarginalRateTaxScale":
        """Scale all the MarginalRateTaxScales in the node."""
        scaled_tax_scale = self.copy()
        return scaled_tax_scale.multiply_thresholds(factor)

    def to_average(self) -> "LinearAverageRateTaxScale":
        average_tax_scale = LinearAverageRateTaxScale(
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


# TODO: there's a circular dependency when importing ParameterNodeAtInstant.
#
# As this is just a helper method, we should move it somewhere else, like for example:
#
#   openfisca_core/commons.py
#   openfisca_core/formula_helpers.py
#
def combine_tax_scales(
        node,  # node: ParameterNodeAtInstant
        combined_tax_scales: Optional["MarginalRateTaxScale"] = None,
        ) -> Optional["MarginalRateTaxScale"]:
    """
    Combine all the MarginalRateTaxScales in the node into a single
    MarginalRateTaxScale.
    """

    name = next(iter(node or []), None)

    if name is None:
        return combined_tax_scales

    if combined_tax_scales is None:
        combined_tax_scales = MarginalRateTaxScale(name = name)
        combined_tax_scales.add_bracket(0, 0)

    for child_name in node:
        child = node[child_name]

        if isinstance(child, MarginalRateTaxScale):
            combined_tax_scales.add_tax_scale(child)

        else:
            log.info(
                f"Skipping {child_name} with value {child} "
                "because it is not a marginal rate tax scale",
                )

    return combined_tax_scales
