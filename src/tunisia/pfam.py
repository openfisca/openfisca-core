# -*- coding:utf-8 -*-
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

"""
openFisca, Logiciel libre de simulation du système socio-fiscal français
Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

This file is part of openFisca.

    openFisca is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    openFisca is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with openFisca.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import division
from numpy import (round, floor, zeros, maximum as max_, minimum as min_,
                   logical_not as not_)
from tunisia.data import QUIFAM


CHEF = QUIFAM['chef']
PART = QUIFAM['part']
ENFS = [QUIFAM['enf1'], QUIFAM['enf2'], QUIFAM['enf3'], QUIFAM['enf4'], QUIFAM['enf5'], QUIFAM['enf6'], QUIFAM['enf7'], QUIFAM['enf8'], QUIFAM['enf9'], ]

def _nb_par(quifam, _option={'quifam':[PART]}):
    '''
    Nombre d'adultes (parents) dans la famille
    'fam'
    '''
    return 1 + 1 * (quifam[PART] == 1) 
    
def _maries(statmarit):
    '''
    couple = 1 si couple marié sinon 0 TODO faire un choix avec couple ? 
    '''
    return statmarit == 1

def _concub(nb_par):
    '''
    concub = 1 si vie en couple TODO pas très heureux  
    '''
    # TODO: concub n'est pas égal à 1 pour les conjoints
    return nb_par == 2

def _isol(nb_par):
    '''
    Parent (s'il y a lieu) isolé  
    '''
    return nb_par == 1

def _etu(activite):
    '''
    Indicatrice individuelle etudiant
    ''' 
    return activite == 2



############################################################################
# Allocations familiales
############################################################################
    
def _af_base(af_nbenf, _P):
    '''
    Allocations familiales - allocation de base
    'fam'
    '''
    P = _P.fam
    bm = P.af.plaf_trim/3 # base mensuelle    
    # prestations familliales 
    af_1enf = round(bm * P.af.taux.enf1, 2)
    af_2enf = round(bm * P.af.taux.enf2, 2)
    af_3enf = round(bm * P.af.taux.enf3, 2)
    af_base = (af_nbenf >= 1)*af_1enf + (af_nbenf >= 2)*af_2enf + (af_nbenf==3)*af_3enf
    return 12 * af_base  # annualisé

def _af_sal_uniq(age, af_nbenf, smic55, _P, _option={'age': ENFS, 'smic55': ENFS}):
    '''
    Allocations familiales - majoration salaire unique
    'fam'
    '''
    # TODO
    return 0


def _af_cong_naiss(age, _P, _option={'age': ENFS}):
    return 0

def _af_cong_jeun_trav(age, _P, _option={'age': ENFS}):
    return 0

    
def _af_creche(age, _P, _option={'age': ENFS}):
    '''
    Allocations familiales - contribution au frais de crêche
    'fam'
    '''
    return 0


def _af(af_base, af_sal_uniq, _af_cong_naiss, af_cong_jeun_trav, af_creche):
    '''
    Allocations familiales - total des allocations
    'fam'
    '''
    return af_base + af_sal_uniq + _af_cong_naiss + af_cong_jeun_trav + af_creche

############################################################################
# Assurances sociales   Maladie
############################################################################

def _as_mal(age, sal, _P, _option={'age': ENFS}):
    '''
    Assurance sociale - prestation en espèces TODO
    ''' 
#    P = _P.as.mal 
    P = 0
    mal = 0
    smig = _P.gen.smig
    return mal*P.part*max(P.plaf_mult*smig,sal)*P.duree


def _as_maternite(age, sal, _P, _option={'age': ENFS}):
    '''
    Assurance sociale - maternité  TODO
    'fam' 
    '''
    # P = _P.as.mat 
    smig = _P.gen.smig
    #return P.part*max(P.plaf_mult*smig,sal)*P.duree
    return 0

def _as_deces(sal, _P, _option={'age': ENFS}):
    '''
    Assurance sociale - décès   # TODO
    'fam'
    '''
    # P = _P.as.dec
    return 0


