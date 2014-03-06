# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
# https://github.com/openfisca
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


class Bareme(object):
    '''
    Object qui contient des tranches d'imposition en taux marginaux et en taux moyen
    '''
    def __init__(self, name = 'untitled Bareme', option = None, unit = None):
        super(Bareme, self).__init__()
        self._name = name
        self._tranches = []
        self._nb = 0
        self._tranchesM = []
        # if _linear_taux_moy is 'False' (default), the output is computed with a constant marginal tax rate in each bracket
        # set _linear_taux_moy to 'True' to compute the output with a linear interpolation on average tax rate
        self._linear_taux_moy = False
        self._option = option
        self.unit = unit

    @property
    def option(self):
        return self._option

    def setOption(self, option):
        self._option = option

    @property
    def nb(self):
        return self._nb

    @property
    def seuils(self):
        return [x[0] for x in self._tranches]

    @property
    def taux(self):
        return [x[1] for x in self._tranches]

    def setSeuil(self, i, value):
        self._tranches[i][0] = value
        self._tranches.sort()

    def setTaux(self, i, value):
        self._tranches[i][1] = value

    @property
    def seuilsM(self):
        return [x[0] for x in self._tranchesM]

    @property
    def tauxM(self):
        return [x[1] for x in self._tranchesM]

    def setSeuilM(self, i, value):
        self._tranchesM[i][0] = value
        self._tranchesM.sort()

    def setTauxM(self, i, value):
        self._tranchesM[i][1] = value

    def multTaux(self, factor, inplace = True, new_name = None):
        if inplace:
            for i in range(self._nb):
                self.setTaux(i, factor * self.taux[i])
        else:
            if new_name is None:
                new_name = self._name
            b = Bareme(new_name, option = self._option, unit = self.unit)
            for i in range(self.nb):
                b.addTranche(self.seuils[i], self.taux[i])
            b.multTaux(factor, inplace = True)
            return b

    def multSeuils(self, factor):
        '''
        Returns a new instance of Bareme with scaled 'seuils' and same 'taux'
        '''
        b = Bareme(self._name, option = self._option, unit = self.unit)
        for i in range(self.nb):
            b.addTranche(factor * self.seuils[i], self.taux[i])
        return b

    def addBareme(self, bareme):
        if bareme.nb > 0:  # Pour ne pas avoir de problèmes avec les barèmes vides
            for seuilInf, seuilSup, taux  in zip(bareme.seuils[:-1], bareme.seuils[1:] , bareme.taux):
                self.combineTranche(taux, seuilInf, seuilSup)
            self.combineTranche(bareme.taux[-1], bareme.seuils[-1])  # Pour traiter le dernier seuil

    def combineTranche(self, taux, seuilInf = 0, seuilSup = False):
        # Insertion de seuilInf et SeuilSup sans modfifer les taux
        if not seuilInf in self.seuils:
            index = bisect_right(self.seuils, seuilInf) - 1
            self.addTranche(seuilInf, self.taux[index])

        if seuilSup and not seuilSup in self.seuils:
                index = bisect_right(self.seuils, seuilSup) - 1
                self.addTranche(seuilSup, self.taux[index])

        # On utilise addTranche pour ajouter les taux où il le faut
        i = self.seuils.index(seuilInf)
        if seuilSup: j = self.seuils.index(seuilSup) - 1
        else: j = self._nb - 1
        while (i <= j):
            self.addTranche(self.seuils[i], taux)
            i += 1

    def addTranche(self, seuil, taux):
        if seuil in self.seuils:
            i = self.seuils.index(seuil)
            self.setTaux(i, self.taux[i] + taux)
        else:
            self._tranches.append([seuil, taux])
            self._tranches.sort()
            self._nb = len(self._tranches)

    def rmvTranche(self):
        self._tranches.pop()
        self._nb = len(self._tranches)

    def addTrancheM(self, seuil, taux):
        if seuil in self.seuilsM:
            i = self.seuilsM.index(seuil)
            self.setTauxM(i, self.tauxM[i] + taux)
        else:
            self._tranchesM.append([seuil, taux])

    def marToMoy(self):
        self._tranchesM = []
        I, k = 0, 0
        if self.nb > 0:
            for seuil, taux in self:
                if k == 0:
                    sprec = seuil
                    tprec = taux
                    k += 1
                    continue
                I += tprec * (seuil - sprec)
                self.addTrancheM(seuil, I / seuil)
                sprec = seuil
                tprec = taux
            self.addTrancheM('Infini', taux)

    def moyToMar(self):
        self._tranches = []
        Iprev, sprev = 0, 0
        z = zip(self.seuilsM, self.tauxM)
        for seuil, taux in z:
            if not seuil == 'Infini':
                I = taux * seuil
                self.addTranche(sprev, (I - Iprev) / (seuil - sprev))
                sprev = seuil
                Iprev = I
        self.addTranche(sprev, taux)

    def inverse(self):
        '''
        Returns a new instance of Bareme
        Inverse un barème: étant donné des tranches et des taux exprimés en fonction
        du brut, renvoie un barème avec les tranches et les taux exprimé en net.
          si revnet  = revbrut - BarmMar(revbrut, B)
          alors revbrut = BarmMar(revnet, B.inverse())
        seuil : seuil de revenu brut
        seuil imposable : seuil de revenu imposable/déclaré
        theta : ordonnée à l'origine des segments des différentes tranches dans une
                représentation du revenu imposable comme fonction linéaire par
                morceaux du revenu brut
        '''
        inverse = Bareme(self._name + "'")  # En fait 1/(1-taux_global)
        seuilImp, taux = 0, 0
        for seuil, taux in self:
            if seuil == 0: theta, tauxp = 0, 0
            # On calcul le seuil de revenu imposable de la tranche considérée
            seuilImp = (1 - tauxp) * seuil + theta
            inverse.addTranche(seuilImp, 1 / (1 - taux))
            theta = (taux - tauxp) * seuil + theta
            tauxp = taux  # taux précédent
        return inverse

    def __iter__(self):
        return itertools.izip(self.seuils, self.taux)

    def __str__(self):
        output = self._name + '\n'
        for i in range(self._nb):
            output += str(self.seuils[i]) + '  ' + str(self.taux[i]) + '\n'
        return output

    def __eq__(self, other):
        return self._tranches == other._tranches

    def __ne__(self, other):
        return self._tranches != other._tranches

    def calc(self, assiette, getT = False):
        '''
        Calcule un impôt selon le barême non linéaire exprimé en tranches de taux marginaux.
        'assiette' est l'assiette de l'impôt, en colonne
        '''
        k = self.nb
        n = len(assiette)
        if not self._linear_taux_moy:
            assi = np.tile(assiette, (k, 1)).T
            seui = np.tile(np.hstack((self.seuils, np.inf)), (n, 1))
            a = max_(min_(assi, seui[:, 1:]) - seui[:, :-1], 0)
            i = np.dot(self.taux, a.T)
            if getT:
                t = np.squeeze(max_(np.dot((a > 0), np.ones((k, 1))) - 1, 0))
                return i, t
            else:
                return i
        else:
            if len(self.tauxM) == 1:
                i = assiette * self.tauxM[0]
            else:
                assi = np.tile(assiette, (k - 1, 1)).T
                seui = np.tile(np.hstack(self.seuils), (n, 1))
                k = self.t_x().T
                a = (assi >= seui[:, :-1]) * (assi < seui[:, 1:])
                A = np.dot(a, self.t_x().T)
                B = np.dot(a, np.array(self.seuils[1:]))
                C = np.dot(a, np.array(self.tauxM[:-1]))
                i = assiette * (A * (assiette - B) + C) + max_(assiette - self.seuils[-1], 0) * self.tauxM[-1] + (assiette >= self.seuils[-1]) * self.seuils[-1] * self.tauxM[-2]
            if getT:
                t = np.squeeze(max_(np.dot((a > 0), np.ones((k, 1))) - 1, 0))
                return i, t
            else:
                return i

    def t_x(self):
        s = self.seuils
        t = [0]
        t.extend(self.tauxM[:-1])
        s = np.array(s)
        t = np.array(t)
        return (t[1:] - t[:-1]) / (s[1:] - s[:-1])


class BaremeDict(dict):
    '''A tree of Baremes'''
    def __init__(self, name = None, compact_node = None):
        super(BaremeDict, self).__init__()

        assert name is not None, "BaremeDict instance needs a name to be created"
        self._name = name

        if compact_node is not None:
            self.init_from_compact_node(compact_node)

    def init_from_compact_node(self, compact_node):
        '''Initialize a BaremeDict from a CompactNode.'''
        from .legislations import CompactNode
        from .parameters import Tree2Object

        if isinstance(compact_node, Bareme):
            self[compact_node._name] = compact_node
        elif isinstance(compact_node, (CompactNode, Tree2Object)):
            for key, bar in compact_node.__dict__.iteritems():
                if isinstance(bar, Bareme):
                    self[key] = bar
                elif isinstance(bar, (CompactNode, Tree2Object)):
                    self[key] = BaremeDict(key, bar)

    def log(self, tabLevel = -1):
        output = ""

        tabLevel += 1
        for i in range(tabLevel):
             output += "\t"

        output += "|------" + self._name + "\n"

        for name, bar in self.iteritems():
            if isinstance(bar, Bareme):
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


def combineBaremes(bardict, name = None):
    '''
    Combine all the Baremes in the BaremeDict in a signle Bareme
    '''
    if name is None:
        name = 'Combined ' + bardict._name
    baremeTot = Bareme(name = name)
    baremeTot.addTranche(0, 0)
    for name, bar in bardict.iteritems():
        if isinstance(bar, Bareme):
            baremeTot.addBareme(bar)
        else:
            combineBaremes(bar, baremeTot)
    return baremeTot


def scaleBaremes(bar_dict, factor):
    '''
    Scales all the Bareme in the BarColl
    '''
    if isinstance(bar_dict, Bareme):
        return bar_dict.multSeuils(factor)

    if isinstance(bar_dict, BaremeDict):
        out = BaremeDict(name = bar_dict._name)

        for key, bar in bar_dict.iteritems():
            if isinstance(bar, Bareme):
                out[key] = bar.multSeuils(factor)
            elif isinstance(bar, BaremeDict):
                out[key] = scaleBaremes(bar, factor)
            else:
                setattr(out, key, bar)
        return out
