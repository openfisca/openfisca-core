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

from bisect import bisect_right
import itertools

import numpy as np
from numpy import maximum as max_, minimum as min_


# Bracket = Tranche
# TaxScale = Bareme


class TaxScale(object):
    '''
    A TaxScale is an object which contains two sets of brackets:
     - brackets for taxation with marginal tax rates
     - brackets_average_rate for taxation at average tax rate
     - brackets_constant_amount for taxation at a constant amount for the whole bracket
    '''

    def __init__(self, name = 'untitled TaxScale', option = None, unit = None, constant_amount_option = False):
        super(TaxScale, self).__init__()
        self._name = name
        self._brackets = []
        self._nb = 0
        self._brackets_average_rate = []
        self.constant_amount_option = constant_amount_option
        self._brackets_constant_amount = []

        # if _linear_avg_rate is 'False' (default), the output is computed with a constant marginal tax rate in each bracket
        # set _linear_avg_rate to 'True' to compute the output with a linear interpolation on average tax rate
        self._linear_avg_rate = False

        self._option = option
        self.unit = unit

    @property
    def option(self):
        return self._option

    def set_option(self, option):
        self._option = option

    @property
    def nb(self):
        return self._nb

    @property
    def thresholds(self):
        return [x[0] for x in self._brackets]

    @property
    def rates(self):
        return [x[1] for x in self._brackets]

    @property
    def constant_amounts(self):
        return [x[1] for x in self._brackets_constant_amount]

    def set_threshold(self, i, value):
        self._brackets[i][0] = value
        self._brackets.sort()

    def set_rate(self, i, value):
        self._brackets[i][1] = value

    def set_amount(self, i, value):
        self._brackets_constant_amount[i][1] = value

    @property
    def thresholds_average(self):
        return [x[0] for x in self._brackets_average_rate]

    @property
    def rates_average(self):
        return [x[1] for x in self._brackets_average_rate]

    def set_threshold_average(self, i, value):
        self._brackets_average_rate[i][0] = value
        self._brackets_average_rate.sort()

    def set_rate_average(self, i, value):
        self._brackets_average_rate[i][1] = value

    @property
    def thresholds_constant_amount(self):
        return [x[0] for x in self._brackets_constant_amount]

    @property
    def constant_amounts(self):
        return [x[1] for x in self._brackets_constant_amount]

    def set_constant_amount(self, i, value):
        self._brackets_constant_amount[i][1] = value

    def multiply_rates(self, factor, inplace = True, new_name = None):
        if inplace:
            for i in range(self._nb):
                self.set_rate(i, factor * self.rates[i])
        else:
            if new_name is None:
                new_name = self._name
            b = TaxScale(new_name, option = self._option, unit = self.unit)
            for i in range(self.nb):
                b.add_bracket(self.thresholds[i], self.rates[i])
            b.multiply_rates(factor, inplace = True)
            return b

    def multiply_thresholds(self, factor):
        '''
        Returns a new instance of TaxScale with scaled thresholds and same rates
        '''
        b = TaxScale(self._name, option = self._option, unit = self.unit)
        for i in range(self.nb):
            b.add_bracket(factor * self.thresholds[i], self.rates[i])
        return b

    def add_tax_scale(self, tax_scale):
        if tax_scale.nb > 0:  # Pour ne pas avoir de problèmes avec les barèmes vides
            for thresholdInf, thresholdSup, rate  in zip(tax_scale.thresholds[:-1], tax_scale.thresholds[1:] , tax_scale.rates):
                self.combine_bracket(rate, thresholdInf, thresholdSup)
            self.combine_bracket(tax_scale.rates[-1], tax_scale.thresholds[-1])  # Pour traiter le dernier threshold

    def combine_bracket(self, rate, thresholdInf = 0, thresholdSup = False):
        # Insert thresholdInf and thresholdSup without modifying rates
        if not thresholdInf in self.thresholds:
            index = bisect_right(self.thresholds, thresholdInf) - 1
            self.add_bracket(thresholdInf, self.rates[index])

        if thresholdSup and not thresholdSup in self.thresholds:
                index = bisect_right(self.thresholds, thresholdSup) - 1
                self.add_bracket(thresholdSup, self.rates[index])

        # Use add_bracket to add rates where they belongs
        i = self.thresholds.index(thresholdInf)
        if thresholdSup: j = self.thresholds.index(thresholdSup) - 1
        else: j = self._nb - 1
        while (i <= j):
            self.add_bracket(self.thresholds[i], rate)
            i += 1

    def add_bracket(self, threshold, rate):
        if threshold in self.thresholds:
            i = self.thresholds.index(threshold)
            self.set_rate(i, self.rates[i] + rate)
        else:
            self._brackets.append([threshold, rate])
            self._brackets.sort()
            self._nb = len(self._brackets)

    def remove_bracket(self):
        self._brackets.pop()
        self._nb = len(self._brackets)

    def add_bracket_average(self, threshold, rate):
        if threshold in self.thresholds_average:
            i = self.thresholds_average.index(threshold)
            self.set_rate_average(i, self.rates_average[i] + rate)
        else:
            self._brackets_average_rate.append([threshold, rate])

    def add_bracket_constant_amount(self, threshold, amount):
        if threshold in self.thresholds_constant_amount:
            i = self.thresholds_constant_amount.index(threshold)
            self.set_constant_amount(i, self.constant_amounts[i] + amount)
        else:
            self._brackets_constant_amount.append([threshold, amount])

    def marginal_to_average(self):
        self._brackets_average_rate = []
        I, k = 0, 0
        if self.nb > 0:
            for threshold, rate in self:
                if k == 0:
                    sprec = threshold
                    tprec = rate
                    k += 1
                    continue
                I += tprec * (threshold - sprec)
                self.add_bracket_average(threshold, I / threshold)
                sprec = threshold
                tprec = rate
            self.add_bracket_average('Infini', rate)

    def average_to_marginal(self):
        self._brackets = []
        Iprev, sprev = 0, 0
        z = zip(self.thresholds_average, self.rates_average)
        for threshold, rate in z:
            if not threshold == 'Infini':
                I = rate * threshold
                self.add_bracket(sprev, (I - Iprev) / (threshold - sprev))
                sprev = threshold
                Iprev = I
        self.add_bracket(sprev, rate)

    def inverse(self):
        '''
        Returns a new instance of TaxScale
        Inverse un barème: étant donné des brackets et des rates exprimés en fonction
        du brut, renvoie un barème avec les brackets et les rates exprimés en net.
          si revnet  = revbrut - BarmMar(revbrut, B)
          alors revbrut = BarmMar(revnet, B.inverse())
        threshold : threshold de revenu brut
        threshold imposable : threshold de revenu imposable/déclaré
        theta : ordonnée à l'origine des segments des différentes brackets dans une
                représentation du revenu imposable comme fonction linéaire par
                morceaux du revenu brut
        '''
        inverse = TaxScale(name = self._name + "'")  # Actually 1/(1-global-rate)
        thresholdImp, rate = 0, 0
        for threshold, rate in self:
            if threshold == 0: theta, rate_previous = 0, 0
            # On calcul le threshold de revenu imposable de la tranche considérée
            thresholdImp = (1 - rate_previous) * threshold + theta
            inverse.add_bracket(thresholdImp, 1 / (1 - rate))
            theta = (rate - rate_previous) * threshold + theta
            rate_previous = rate  # previous rate
        return inverse

    def __eq__(self, other):
        return self._brackets == other._brackets

    def __iter__(self):
        return itertools.izip(self.thresholds, self.rates)

    def __ne__(self, other):
        return self._brackets != other._brackets

    def __str__(self):
        output = self._name + '\n'
        for i in range(self._nb):
            output += str(self.thresholds[i]) + '  ' + str(self.rates[i]) + '\n'
        return output

    def calc(self, base, getT = False):
        if self.constant_amount_option is True:
            assi = np.tile(base, (k, 1)).T
            seui = np.tile(np.hstack((self.thresholds, np.inf)), (n, 1))
            a = max_(min_(assi, seui[:, 1:]) - seui[:, :-1], 0)
            i = np.dot(self.constant_amounts, a.T > 0)
            return i
        else:
            return self.calculate(base, getT = getT)

    def calculate(self, base, getT = False):
        '''
        Computes the tax using a a nonlinear tax scale using marginal tax rates
        Note: base is the base of the tax, in column
        '''
        k = self.nb
        n = len(base)
        if not self._linear_avg_rate:
            assi = np.tile(base, (k, 1)).T
            seui = np.tile(np.hstack((self.thresholds, np.inf)), (n, 1))
            a = max_(min_(assi, seui[:, 1:]) - seui[:, :-1], 0)
            i = np.dot(self.rates, a.T)
            if getT:
                t = np.squeeze(max_(np.dot((a > 0), np.ones((k, 1))) - 1, 0))
                return i, t
            else:
                return i
        else:
            if len(self.rates_average) == 1:
                i = base * self.rates_average[0]
            else:
                assi = np.tile(base, (k - 1, 1)).T
                seui = np.tile(np.hstack(self.thresholds), (n, 1))
                k = self.t_x().T
                a = (assi >= seui[:, :-1]) * (assi < seui[:, 1:])
                A = np.dot(a, self.t_x().T)
                B = np.dot(a, np.array(self.thresholds[1:]))
                C = np.dot(a, np.array(self.rates_average[:-1]))
                i = base * (A * (base - B) + C) + max_(base - self.thresholds[-1], 0) * self.rates_average[-1] + (base >= self.thresholds[-1]) * self.thresholds[-1] * self.rates_average[-2]
            if getT:
                t = np.squeeze(max_(np.dot((a > 0), np.ones((k, 1))) - 1, 0))
                return i, t
            else:
                return i

    def t_x(self):
        s = self.thresholds
        t = [0]
        t.extend(self.rates_average[:-1])
        s = np.array(s)
        t = np.array(t)
        return (t[1:] - t[:-1]) / (s[1:] - s[:-1])


class TaxScaleDict(dict):
    '''A tree of TaxScales'''
    def __init__(self, name = None, compact_node = None):
        super(TaxScaleDict, self).__init__()

        assert name is not None, "TaxScaleDict instance needs a name to be created"
        self._name = name

        if compact_node is not None:
            self.init_from_compact_node(compact_node)

    def init_from_compact_node(self, compact_node):
        '''Initialize a TaxScaleDict from a CompactNode.'''
        from .legislations import CompactNode
        from .parameters import Tree2Object

        if isinstance(compact_node, TaxScale):
            self[compact_node._name] = compact_node
        elif isinstance(compact_node, (CompactNode, Tree2Object)):
            for key, bar in compact_node.__dict__.iteritems():
                if isinstance(bar, TaxScale):
                    self[key] = bar
                elif isinstance(bar, (CompactNode, Tree2Object)):
                    self[key] = TaxScaleDict(key, bar)

    def log(self, tabLevel = -1):
        output = ""

        tabLevel += 1
        for i in range(tabLevel):
             output += "\t"

        output += "|------" + self._name + "\n"

        for name, bar in self.iteritems():
            if isinstance(bar, TaxScale):
                for i in range(tabLevel + 1):
                    output += "\t"
                output += "|------" + bar.__str__() + '\n'
            else:
                output += bar.log(tabLevel)

        tabLevel -= 1
        output += "\n"
        return output

    def __repr__(self):
        return self.log()


def combine_tax_scales(bardict, name = None):
    '''
    Combine all the TaxScales in the TaxScaleDict in a signle TaxScale
    '''
    if name is None:
        name = 'Combined ' + bardict._name
    tax_scaleTot = TaxScale(name = name)
    tax_scaleTot.add_bracket(0, 0)
    for name, bar in bardict.iteritems():
        if isinstance(bar, TaxScale):
            tax_scaleTot.add_tax_scale(bar)
        else:
            combine_tax_scales(bar, tax_scaleTot)
    return tax_scaleTot


def scale_tax_scales(bar_dict, factor):
    '''
    Scales all the TaxScale in the BarColl
    '''
    if isinstance(bar_dict, TaxScale):
        return bar_dict.multiply_thresholds(factor)

    if isinstance(bar_dict, TaxScaleDict):
        out = TaxScaleDict(name = bar_dict._name)

        for key, bar in bar_dict.iteritems():
            if isinstance(bar, TaxScale):
                out[key] = bar.multiply_thresholds(factor)
            elif isinstance(bar, TaxScaleDict):
                out[key] = scale_tax_scales(bar, factor)
            else:
                setattr(out, key, bar)
        return out
