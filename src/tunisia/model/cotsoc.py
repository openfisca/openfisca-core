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

from numpy import  zeros, logical_not as not_
from core.utils import scaleBaremes, combineBaremes
from core.utils import  scaleBaremes, combineBaremes, BaremeDict


from tunisia.model.data import CAT
class Object(object):
    def __init__(self):
        object.__init__(self)
                
# TODO: CHECK la csg déductible en 2006 est case GH
# TODO:  la revenus soumis aux csg déductible et imposable sont en CG et BH en 2010 

#        # Heures supplémentaires exonérées
#        if not self.bareme.ir.autre.hsup_exo:
#            self.sal += self.hsup
#            self.hsup = 0*self.hsup
                        
# Exonération de CSG et de CRDS sur les revenus du chômage 
# et des préretraites si cela abaisse ces revenus sous le smic brut        
# TODO mettre un trigger pour l'éxonération des revenus du chômage sous un smic

# TODO RAFP assiette = prime
# TODO pension assiette = salaire hors prime
# autres salaires + primes
# TODO personnels non titulaires IRCANTEC etc

# TODO contribution patronale de prévoyance complémentaire
# Formation professionnelle (entreprise de 10 à moins de 20 salariés) salaire total 1,05%
# Formation professionnelle (entreprise de moins de 10 salariés)      salaire total 0,55%
# Taxe sur les salaries (pour ceux non-assujettis à la TVA)           salaire total 4,25% 
# TODO accident du travail ?
    
#temp = 0
#if hasattr(P, "prelsoc"):
#    for val in P.prelsoc.__dict__.itervalues(): temp += val
#    P.prelsoc.total = temp         
#else : 
#    P.__dict__.update({"prelsoc": {"total": 0} })
#
#a = {'sal':sal, 'pat':pat, 'csg':csg, 'crds':crds, 'exo_fillon': P.cotsoc.exo_fillon, 'lps': P.lps, 'ir': P.ir, 'prelsoc': P.prelsoc}
#return Dicts2Object(**a)



############################################################################
## Salaires
############################################################################

def _salbrut(sali, type_sal, _defaultP):
    '''
    Calcule le salaire brut à partir du salaire net
    '''
    
    smig = _defaultP.cotsoc.gen.smig_40h
    cotsoc = BaremeDict('cotsoc', _defaultP.cotsoc)
    
    plaf_ss = 12*smig

    n = len(sali)
    salbrut = zeros(n)
    for categ in CAT:
        iscat = (type_sal == categ[1])
        if 'sal' in  cotsoc[categ[0]]:
            sal = cotsoc[categ[0]]['sal']
            baremes = scaleBaremes(sal, plaf_ss)
            bar = combineBaremes(baremes)
            invbar = bar.inverse()
            temp =  iscat*(invbar.calc(sali))
            salbrut += temp
    return salbrut 
    

def _salsuperbrut(salbrut, cotpat):
    '''
    Salaire superbrut
    '''
    return salbrut - cotpat

def _cotpat(salbrut, type_sal, _P):
    '''
    Cotisation sociales patronales
    '''
    # TODO traiter les différents régimes séparément ?


    smig = _P.cotsoc.gen.smig_40h
    cotsoc = BaremeDict('cotsoc', _P.cotsoc)
    
    plaf_ss = 12*smig

    
    n = len(salbrut)
    cotpat = zeros(n)
    for categ in CAT:
        iscat = (type_sal == categ[1])
        if 'pat' in  cotsoc[categ[0]]:
            pat = cotsoc[categ[0]]['pat']
            baremes = scaleBaremes(pat, plaf_ss)
            bar = combineBaremes(baremes)
            temp = - (iscat*bar.calc(salbrut))
            cotpat += temp
    return cotpat


def _cotsal(salbrut, type_sal, _P):
    '''
    Cotisations sociales salariales
    '''
    # TODO traiter les différents régimes
    
    smig = _P.cotsoc.gen.smig_40h
    cotsoc = BaremeDict('cotsoc', _P.cotsoc)    
    plaf_ss = 12*smig

    n = len(salbrut)
    cotsal = zeros(n)
    
    for categ in CAT:
        iscat = (type_sal == categ[1])
        if 'sal' in  cotsoc[categ[0]]:
            pat = cotsoc[categ[0]]['sal']
            baremes = scaleBaremes(pat, plaf_ss)
            bar = combineBaremes(baremes)
            temp = - (iscat*bar.calc(salbrut))
            cotsal += temp
        
    return cotsal
