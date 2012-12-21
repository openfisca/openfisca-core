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
from numpy import (floor, arange)
from tunisia.model.data import  QUIMEN

ALL = [x[1] for x in QUIMEN]

def _uc(agem, _option = {'agem': ALL}):
    '''
    Calcule le nombre d'unités de consommation du ménage avec l'échelle de l'insee
    'men'
    '''
    uc_adt = 0.5
    uc_enf = 0.3
    uc = 0.5
    for agm in agem.itervalues():
        age = floor(agm/12)
        adt = (15 <= age) & (age <= 150)
        enf = (0  <= age) & (age <= 14)
        uc += adt*uc_adt + enf*uc_enf
    return uc

#def _typ_men(isol, af_nbenf):
#    '''
#    type de menage
#    'men'
#    TODO: prendre les enfants du ménages et non ceux de la famille
#    '''
#    _0_kid = af_nbenf == 0
#    _1_kid = af_nbenf == 1
#    _2_kid = af_nbenf == 2
#    _3_kid = af_nbenf >= 3
#    
#    return (0*(isol & _0_kid) + # Célibataire
#            1*(not_(isol) & _0_kid) + # Couple sans enfants
#            2*(not_(isol) & _1_kid) + # Couple un enfant
#            3*(not_(isol) & _2_kid) + # Couple deux enfants
#            4*(not_(isol) & _3_kid) + # Couple trois enfants et plus
#            5*(isol & _1_kid) + # Famille monoparentale un enfant
#            6*(isol & _2_kid) + # Famille monoparentale deux enfants
#            7*(isol & _3_kid) ) # Famille monoparentale trois enfants et plus
            
    
def _revdisp_i(rev_trav, pen, rev_cap, psoc, impo):
    '''
    Revenu disponible
    'ind'
    '''
    return rev_trav + pen + rev_cap + psoc + impo

def _revdisp(revdisp_i, _option = {'revdisp_i': ALL}):
    '''
    Revenu disponible - ménage
    'men'
    '''
    r = 0
    for rev in revdisp_i.itervalues():
        r += rev
    return r

def _nivvie(revdisp, uc):
    '''
    Niveau de vie du ménage
    'men'
    '''
    return revdisp/uc

def _rev_trav(sali):
    '''Revenu du travail'''
    return sali #+ beap + bic + bnc  TODO

#def _pen(rstnet, alr, alv, rto):
#    '''Pensions'''
#    return rstnet #+ alr + alv + rto TODO
#
#def _rstnet(pen):
#    '''Retraites nettes'''
#    return pen 

def _rev_cap(rfon):
    '''Revenus du patrimoine'''  # TODO
    return rfon
 
#def _psoc(pfam):
#    '''Prestations sociales'''
#    return pfam
#
#def _pfam(af,s):
#    ''' Prestations familiales '''
#    return af


def _impo(irpp):
    '''Impôts directs'''
    return irpp

from core.utils import mark_weighted_percentiles

def _decile(nivvie, wprm):
    '''
    Décile de niveau de vie
    'men'
    '''
    labels = arange(1,11)
    method = 2
    decile = mark_weighted_percentiles(nivvie, labels, wprm, method, return_quantiles=False)
    return decile
