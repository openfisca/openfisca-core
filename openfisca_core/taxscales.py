# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
# https://github.com/openxfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import division

from bisect import bisect_left, bisect_right
import itertools

import numpy as np
from numpy import maximum as max_, minimum as min_


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

    def __str__(self):
        raise NotImplementedError('Method "__str__" is not implemented for {}'.format(self.__class__.__name__))

    def calc(self, base):
        raise NotImplementedError('Method "calc" is not implemented for {}'.format(self.__class__.__name__))


class AbstractRateTaxScale(AbstractTaxScale):
    """Abstract class for various types of rate-based tax scales (marginal rate, linear average rate)"""
    rates = None

    def __init__(self, name = None, option = None, unit = None):
        super(AbstractRateTaxScale, self).__init__(name = name, option = option, unit = unit)
        self.rates = []

    def __str__(self):
        return '\n'.join(itertools.chain(
            ['{}: {}'.format(self.__class__.__name__, self.name)],
            (
                '- {}  {}'.format(threshold, rate)
                for threshold, rate in itertools.izip(self.thresholds, self.rates)
                ),
            ))

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
        for threshold, rate in itertools.izip(self.thresholds, self.rates):
            new_tax_scale.thresholds.append(threshold)
            new_tax_scale.rates.append(rate * factor)
        return new_tax_scale

    def multiply_thresholds(self, factor, inplace = True, new_name = None):
        if inplace:
            assert new_name is None
            for i, threshold in enumerate(self.thresholds):
                self.thresholds[i] = threshold * factor
            return self

        new_tax_scale = self.__class__(new_name or self.name, option = self.option, unit = self.unit)
        for threshold, rate in itertools.izip(self.thresholds, self.rates):
            new_tax_scale.thresholds.append(threshold * factor)
            new_tax_scale.rates.append(rate)
        return new_tax_scale


class AmountTaxScale(AbstractTaxScale):
    amounts = None

    def __init__(self, name = None, option = None, unit = None):
        super(AmountTaxScale, self).__init__(name = name, option = option, unit = unit)
        self.amounts = []

    def __str__(self):
        return '\n'.join(itertools.chain(
            ['{}: {}'.format(self.__class__.__name__, self.name)],
            (
                '- {}  {}'.format(threshold, amount)
                for threshold, amount in itertools.izip(self.thresholds, self.amounts)
                ),
            ))

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
    # def calc(self, base):
    #     if len(self.rates) == 1:
    #         return base * self.rates[0]
    #     base1 = np.tile(base, (len(self.thresholds) - 1, 1)).T
    #     thresholds1 = np.tile(np.hstack(self.thresholds), (len(base), 1))
    #     a = (base1 >= thresholds1[:, :-1]) * (base1 < thresholds1[:, 1:])

    #     rates2 = np.array([0] + self.rates[:-1])
    #     thresholds2 = np.array(self.thresholds)
    #     rate_x = (rates[1:] - rates[:-1]) / (thresholds[1:] - thresholds[:-1])
    #     A = np.dot(a, rate_x.T)

    #     B = np.dot(a, np.array(self.thresholds[1:]))
    #     C = np.dot(a, np.array(self.rates[:-1]))
    #     return base * (A * (base - B) + C) + max_(base - self.thresholds[-1], 0) * self.rates[-1] \
    #         + (base >= self.thresholds[-1]) * self.thresholds[-1] * self.rates[-2]

    def to_marginal(self):
        marginal_tax_scale = MarginalRateTaxScale(name = self.name, option = self.option, unit = self.unit)
        previous_I = 0
        previous_threshold = 0
        for threshold, rate in itertools.izip(self.thresholds, self.rates):
            if threshold != 'Infini':
                I = rate * threshold
                marginal_tax_scale.add_bracket(previous_threshold, (I - previous_I) / (threshold - previous_threshold))
                previous_I = I
                previous_threshold = threshold
        marginal_tax_scale.add_bracket(previous_threshold, rate)
        return marginal_tax_scale


class MarginalRateTaxScale(AbstractRateTaxScale):
    def add_tax_scale(self, tax_scale):
        if tax_scale.thresholds > 0:  # Pour ne pas avoir de problèmes avec les barèmes vides
            for threshold_low, threshold_high, rate in itertools.izip(tax_scale.thresholds[:-1],
                    tax_scale.thresholds[1:], tax_scale.rates):
                self.combine_bracket(rate, threshold_low, threshold_high)
            self.combine_bracket(tax_scale.rates[-1], tax_scale.thresholds[-1])  # Pour traiter le dernier threshold

    def calc(self, base):
        base1 = np.tile(base, (len(self.thresholds), 1)).T
        thresholds1 = np.tile(np.hstack((self.thresholds, np.inf)), (len(base), 1))
        a = max_(min_(base1, thresholds1[:, 1:]) - thresholds1[:, :-1], 0)
        return np.dot(self.rates, a.T)

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

        Inverse un barème: étant donné des seuils et des taux exprimés en fonction
        du brut, renvoie un barème avec les seuils et les taux exprimés en net.
          si revnet  = revbrut - BarmMar(revbrut, B)
          alors revbrut = BarmMar(revnet, B.inverse())
        threshold : threshold de revenu brut
        taxable threshold imposable : threshold de revenu imposable/déclaré
        theta : ordonnée à l'origine des segments des différents seuils dans une
                représentation du revenu imposable comme fonction linéaire par
                morceaux du revenu brut
        """
        # Actually 1/(1-global-rate)
        inverse = self.__class__(name = self.name + "'", option = self.option, unit = self.unit)
        taxable_threshold = 0
        for threshold, rate in itertools.izip(self.thresholds, self.rates):
            if threshold == 0:
                previous_rate = 0
                theta = 0
            # On calcule le seuil de revenu imposable de la tranche considérée.
            taxable_threshold = (1 - previous_rate) * threshold + theta
            inverse.add_bracket(taxable_threshold, 1 / (1 - rate))
            theta = (rate - previous_rate) * threshold + theta
            previous_rate = rate
        return inverse

    def to_average(self):
        average_tax_scale = LinearAverageRateTaxScale(name = self.name, option = self.option, unit = self.unit)
        if self.thresholds:
            I = 0
            previous_threshold = self.thresholds[0]
            previous_rate = self.rates[0]
            for threshold, rate in itertools.islice(itertools.izip(self.thresholds, self.rates), 1, None):
                I += previous_rate * (threshold - previous_threshold)
                average_tax_scale.add_bracket(threshold, I / threshold)
                previous_threshold = threshold
                previous_rate = rate
            average_tax_scale.add_bracket('Infini', rate)
        return average_tax_scale


class TaxScalesTree(dict):
    '''A tree of MarginalRateTaxScales'''
    def __init__(self, name = None, compact_node = None):
        super(TaxScalesTree, self).__init__()

        assert name is not None, "TaxScalesTree instance needs a name to be created"
        self.name = name

        if compact_node is not None:
            self.init_from_compact_node(compact_node)

    def __repr__(self):
        return self.log()

    def init_from_compact_node(self, compact_node):
        '''Initialize a TaxScalesTree from a CompactNode.'''
        from .legislations import CompactNode

        if isinstance(compact_node, MarginalRateTaxScale):
            self[compact_node.name] = compact_node
        elif isinstance(compact_node, CompactNode):
            for key, tax_scale in compact_node.__dict__.iteritems():
                if isinstance(tax_scale, MarginalRateTaxScale):
                    self[key] = tax_scale
                elif isinstance(tax_scale, CompactNode):
                    self[key] = TaxScalesTree(key, tax_scale)

    def log(self, tab_level = -1):
        output = ""

        tab_level += 1
        for i in range(tab_level):
            output += "\t"

        output += "|------" + self.name + "\n"

        for name, tax_scale in self.iteritems():
            if isinstance(tax_scale, MarginalRateTaxScale):
                for i in range(tab_level + 1):
                    output += "\t"
                output += "|------" + tax_scale.__str__() + '\n'
            else:
                output += tax_scale.log(tab_level)

        tab_level -= 1
        output += "\n"
        return output


def combine_tax_scales(tax_scales_tree, name = None):
    '''Combine all the MarginalRateTaxScales in the TaxScalesTree into a single MarginalRateTaxScale'''
    if name is None:
        name = 'Combined ' + tax_scales_tree.name
    combined_tax_scales = MarginalRateTaxScale(name = name)
    combined_tax_scales.add_bracket(0, 0)
    for name, tax_scale in tax_scales_tree.iteritems():
        if isinstance(tax_scale, MarginalRateTaxScale):
            combined_tax_scales.add_tax_scale(tax_scale)
        else:
            combine_tax_scales(tax_scale, combined_tax_scales)
    return combined_tax_scales


def scale_tax_scales(tax_scales_tree, factor):
    '''
    Scales all the MarginalRateTaxScale in the BarColl
    '''
    if isinstance(tax_scales_tree, MarginalRateTaxScale):
        return tax_scales_tree.multiply_thresholds(factor)

    if isinstance(tax_scales_tree, TaxScalesTree):
        out = TaxScalesTree(name = tax_scales_tree.name)

        for key, tax_scale in tax_scales_tree.iteritems():
            if isinstance(tax_scale, MarginalRateTaxScale):
                out[key] = tax_scale.multiply_thresholds(factor)
            elif isinstance(tax_scale, TaxScalesTree):
                out[key] = scale_tax_scales(tax_scale, factor)
            else:
                setattr(out, key, tax_scale)
        return out
