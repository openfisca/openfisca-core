# -*- coding: utf-8 -*-


from __future__ import unicode_literals, print_function, division, absolute_import

from bisect import bisect_left, bisect_right
import copy
import logging
import itertools
import os

import numpy as np
from numpy import maximum as max_, minimum as min_

from openfisca_core.commons import empty_clone
from openfisca_core.tools import indent

log = logging.getLogger(__name__)


class AbstractTaxScale(object):
    """Abstract class for various types of tax scales (amount-based tax scales, rate-based tax scales)

    French translations:
      * base: assiette
      * bracket: tranche
      * rate: taux
      * tax scale: barème
      * threshold: seuil
    """
    name = None
    option = None
    thresholds = None
    unit = None

    def __init__(self, name = None, option = None, unit = None):
        self.name = name or 'Untitled TaxScale'
        if option is not None:
            self.option = option
        self.thresholds = []
        if unit is not None:
            self.unit = unit

    def __eq__(self, other):
        raise NotImplementedError('Method "__eq__" is not implemented for {}'.format(self.__class__.__name__))

    def __ne__(self, other):
        raise NotImplementedError('Method "__ne__" is not implemented for {}'.format(self.__class__.__name__))

    def __repr__(self):
        raise NotImplementedError('Method "__repr__" is not implemented for {}'.format(self.__class__.__name__))

    def calc(self, base):
        raise NotImplementedError('Method "calc" is not implemented for {}'.format(self.__class__.__name__))

    def copy(self):
        new = empty_clone(self)
        new.__dict__ = copy.deepcopy(self.__dict__)
        return new


class AbstractRateTaxScale(AbstractTaxScale):
    """Abstract class for various types of rate-based tax scales (marginal rate, linear average rate)"""
    rates = None

    def __init__(self, name = None, option = None, unit = None):
        super(AbstractRateTaxScale, self).__init__(name = name, option = option, unit = unit)
        self.rates = []

    def __repr__(self):
        return indent(os.linesep.join([
            '- threshold: {}{}  rate: {}'.format(threshold, os.linesep, rate)
            for (threshold, rate) in zip(self.thresholds, self.rates)
            ]))

    def add_bracket(self, threshold, rate):
        if threshold in self.thresholds:
            i = self.thresholds.index(threshold)
            self.rates[i] += rate
        else:
            i = bisect_left(self.thresholds, threshold)
            self.thresholds.insert(i, threshold)
            self.rates.insert(i, rate)

    def multiply_rates(self, factor, inplace = True, new_name = None):
        if inplace:
            assert new_name is None
            for i, rate in enumerate(self.rates):
                self.rates[i] = rate * factor
            return self

        new_tax_scale = self.__class__(new_name or self.name, option = self.option, unit = self.unit)
        for threshold, rate in zip(self.thresholds, self.rates):
            new_tax_scale.thresholds.append(threshold)
            new_tax_scale.rates.append(rate * factor)
        return new_tax_scale

    def multiply_thresholds(self, factor, decimals = None, inplace = True, new_name = None):
        if inplace:
            assert new_name is None
            for i, threshold in enumerate(self.thresholds):
                if decimals is not None:
                    self.thresholds[i] = np.around(threshold * factor, decimals = decimals)
                else:
                    self.thresholds[i] = threshold * factor
            return self

        new_tax_scale = self.__class__(new_name or self.name, option = self.option, unit = self.unit)
        for threshold, rate in zip(self.thresholds, self.rates):
            if decimals is not None:
                new_tax_scale.thresholds.append(np.around(threshold * factor, decimals = decimals))
            else:
                new_tax_scale.thresholds.append(threshold * factor)

            new_tax_scale.rates.append(rate)
        return new_tax_scale


class AmountTaxScale(AbstractTaxScale):
    amounts = None

    def __init__(self, name = None, option = None, unit = None):
        super(AmountTaxScale, self).__init__(name = name, option = option, unit = unit)
        self.amounts = []

    def __repr__(self):
        from .parameters import indent  # Need to import here to avoid a circular dependency
        return indent(os.linesep.join([
            '- threshold: {}{}  amount: {}'.format(threshold, os.linesep, amount)
            for (threshold, amount) in zip(self.thresholds, self.amounts)
            ]))

    def add_bracket(self, threshold, amount):
        if threshold in self.thresholds:
            i = self.thresholds.index(threshold)
            self.amounts[i] += amount
        else:
            i = bisect_left(self.thresholds, threshold)
            self.thresholds.insert(i, threshold)
            self.amounts.insert(i, amount)

    def calc(self, base):
        base1 = np.tile(base, (len(self.thresholds), 1)).T
        thresholds1 = np.tile(np.hstack((self.thresholds, np.inf)), (len(base), 1))
        a = max_(min_(base1, thresholds1[:, 1:]) - thresholds1[:, :-1], 0)
        return np.dot(self.amounts, a.T > 0)


class LinearAverageRateTaxScale(AbstractRateTaxScale):
    def calc(self, base):
        if len(self.rates) == 1:
            return base * self.rates[0]

        tiled_base = np.tile(base, (len(self.thresholds) - 1, 1)).T
        tiled_thresholds = np.tile(self.thresholds, (len(base), 1))
        bracket_dummy = (tiled_base >= tiled_thresholds[:, :-1]) * (tiled_base < tiled_thresholds[:, 1:])
        rates_array = np.array(self.rates)
        thresholds_array = np.array(self.thresholds)
        rate_slope = (rates_array[1:] - rates_array[:-1]) / (thresholds_array[1:] - thresholds_array[:-1])
        average_rate_slope = np.dot(bracket_dummy, rate_slope.T)

        bracket_average_start_rate = np.dot(bracket_dummy, rates_array[:-1])
        bracket_threshold = np.dot(bracket_dummy, thresholds_array[:-1])
        log.info("bracket_average_start_rate :  {}".format(bracket_average_start_rate))
        log.info("average_rate_slope:  {}".format(average_rate_slope))
        return base * (bracket_average_start_rate + (base - bracket_threshold) * average_rate_slope)

    def to_marginal(self):
        marginal_tax_scale = MarginalRateTaxScale(name = self.name, option = self.option, unit = self.unit)
        previous_i = 0
        previous_threshold = 0
        for threshold, rate in zip(self.thresholds[1:], self.rates[1:]):
            if threshold != float('Inf'):
                i = rate * threshold
                marginal_tax_scale.add_bracket(previous_threshold, (i - previous_i) / (threshold - previous_threshold))
                previous_i = i
                previous_threshold = threshold
        marginal_tax_scale.add_bracket(previous_threshold, rate)
        return marginal_tax_scale


class MarginalRateTaxScale(AbstractRateTaxScale):
    def add_tax_scale(self, tax_scale):
        if len(tax_scale.thresholds) > 0:  # Pour ne pas avoir de problèmes avec les barèmes vides
            for threshold_low, threshold_high, rate in zip(tax_scale.thresholds[:-1],
                    tax_scale.thresholds[1:], tax_scale.rates):
                self.combine_bracket(rate, threshold_low, threshold_high)
            self.combine_bracket(tax_scale.rates[-1], tax_scale.thresholds[-1])  # Pour traiter le dernier threshold

    def calc(self, base, factor = 1, round_base_decimals = None):
        base1 = np.tile(base, (len(self.thresholds), 1)).T
        if isinstance(factor, (float, int)):
            factor = np.ones(len(base)) * factor
        # np.finfo(np.float).eps is used to avoid np.nan = 0 * np.inf creation
        thresholds1 = np.outer(factor + np.finfo(np.float).eps, np.array(self.thresholds + [np.inf]))
        if round_base_decimals is not None:
            thresholds1 = np.round(thresholds1, round_base_decimals)
        a = max_(min_(base1, thresholds1[:, 1:]) - thresholds1[:, :-1], 0)
        if round_base_decimals is None:
            return np.dot(self.rates, a.T)
        else:
            r = np.tile(self.rates, (len(base), 1))
            b = np.round(a, round_base_decimals)
            return np.round(r * b, round_base_decimals).sum(axis = 1)

    def combine_bracket(self, rate, threshold_low = 0, threshold_high = False):
        # Insert threshold_low and threshold_high without modifying rates
        if threshold_low not in self.thresholds:
            index = bisect_right(self.thresholds, threshold_low) - 1
            self.add_bracket(threshold_low, self.rates[index])

        if threshold_high and threshold_high not in self.thresholds:
            index = bisect_right(self.thresholds, threshold_high) - 1
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

    def inverse(self):
        """Returns a new instance of MarginalRateTaxScale

        Invert a taxscale:
            Assume tax_scale composed of bracket which thresholds are expressed in term of brut revenue.
            The inverse is another MarginalTaxSclae which thresholds are expressed in terms of net revenue.
            If net  = revbrut - tax_scale.calc(revbrut) then brut = tax_scale.inverse().calc(net)
        """
        # threshold : threshold of brut revenue
        # net_threshold: threshold of net revenue
        # theta : ordonnée à l'origine des segments des différents seuils dans une
        #         représentation du revenu imposable comme fonction linéaire par
        #         morceaux du revenu brut
        # Actually 1 / (1- global_rate)
        inverse = self.__class__(name = self.name + "'", option = self.option, unit = self.unit)
        net_threshold = 0
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

    def scale_tax_scales(self, factor):
        """Scale all the MarginalRateTaxScales in the node."""
        assert isinstance(factor, (float, int))
        scaled_tax_scale = self.copy()
        return scaled_tax_scale.multiply_thresholds(factor)

    def to_average(self):
        average_tax_scale = LinearAverageRateTaxScale(name = self.name, option = self.option, unit = self.unit)
        average_tax_scale.add_bracket(0, 0)
        if self.thresholds:
            i = 0
            previous_threshold = self.thresholds[0]
            previous_rate = self.rates[0]
            for threshold, rate in itertools.islice(zip(self.thresholds, self.rates), 1, None):
                i += previous_rate * (threshold - previous_threshold)
                average_tax_scale.add_bracket(threshold, i / threshold)
                previous_threshold = threshold
                previous_rate = rate

            average_tax_scale.add_bracket(float('Inf'), rate)
        return average_tax_scale


def combine_tax_scales(node):
    """
        Combine all the MarginalRateTaxScales in the node into a single MarginalRateTaxScale.
    """
    combined_tax_scales = None
    for child_name in node:
        child = node[child_name]

        if not isinstance(child, AbstractTaxScale):
            log.info('Skipping {} with value {} because it is not a tax scale'.format(child_name, child))
            continue

        if combined_tax_scales is None:
            combined_tax_scales = MarginalRateTaxScale(name = child_name)
            combined_tax_scales.add_bracket(0, 0)
        combined_tax_scales.add_tax_scale(child)
    return combined_tax_scales
