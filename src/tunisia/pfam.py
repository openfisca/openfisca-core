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
                   logical_xor as xor_)

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

def _smig75(sal, _P):
    '''
    Indicatrice de rémunération inférieur à 55% du smic
    '''
    return sal < _P.cotscoc.gen.smig40

def _sal_uniq(sal, _P, _option = {'sal' : [CHEF, PART]}):
    '''
    Indicatrice de salaire uniue
    '''
    uniq = xor_(sal[CHEF]>0, sal[PART]>0)
    return uniq

############################################################################
# Allocations familiales
############################################################################
    
    
def _af_nbenf(age, smig75, activite, inv, _P, _option={'age': ENFS, 'smig75': ENFS, 'inv': ENFS}):
    '''
    Nombre d'enfants au titre des allocations familiales
    'fam'
    '''
#    From http://www.allocationfamiliale.com/allocationsfamiliales/allocationsfamilialestunisie.htm
#    Jusqu'à l'âge de 16 ans sans conditions.
#    Jusqu'à l'âge de 18 ans pour les enfants en apprentissage qui ne perçoivent pas une rémunération supérieure à 75 % du SMIG.
#    Jusqu'à l'âge de 21 ans pour les enfants qui fréquentent régulièrement un établissement secondaire, supérieur, 
#      technique ou professionnel, à condition que les enfants n'occupent pas d'emplois salariés.
#    Jusqu'à l'âge de 21 ans pour la jeune fille qui remplace sa mère auprès de ses frères et sœurs.
#    Sans limite d'âge et quelque soit leur rang pour les enfants atteints d'une infirmité ou d'une maladie incurable et se trouvant, 
#    de ce fait, dans l'impossibilité permanente et absolue d'exercer un travail lucratif, et pour les handicapés titulaires d'une carte d'handicapé 
#    qui ne sont pas pris en charge intégralement par un organisme public ou privé benéficiant de l'aide de l'Etat ou des collectivités locales.
    res = None    
    if res is None: res = zeros(len(age))
    for key, ag in age.iteritems():
        res =+ ( (ag < 16) + 
                 (ag < 18)*smig75[key]*(activite[key] =='aprenti')  + # TODO apprenti
                 (ag < 21)*(activite[key]=='eleve' | activite[key]=='etudiant') + 
                 inv[key] )  > 1
    return res
    
    
def _af(af_nbenf, sal, _P, _option = {'sal' : [CHEF, PART]} ):
    '''
    Allocations familiales
    'fam'
    '''
    # Le montant trimestriel est calculé en pourcentage de la rémunération globale trimestrielle palfonnée à 122 dinars
    # TODO ajouter éligibilité des parents aux allocations familiales 
    P = _P.pfam
    bm =  min_( max_(sal[CHEF],sal[PART])/4,  P.af.plaf_trim) # base trimestrielle    
    # prestations familliales 
    af_1enf = round(bm * P.af.taux.enf1, 3)
    af_2enf = round(bm * P.af.taux.enf2, 3)
    af_3enf = round(bm * P.af.taux.enf3, 3)
    af_base = (af_nbenf >= 1)*af_1enf + (af_nbenf >= 2)*af_2enf + (af_nbenf >=3 )*af_3enf
    return 4 * af_base  # annualisé



def _maj_sal_uniq(sal_uniq, af_nbenf, _P):
    '''
    Majoration salaire unique
    'fam'
    '''
    P = _P.pfam.af
    af_1enf = round( P.sal_uniq.enf1, 3)
    af_2enf = round( P.sal_uniq.enf2, 3)
    af_3enf = round( P.sal_uniq.enf3, 3)
    af = (af_nbenf >= 1)*af_1enf + (af_nbenf >= 2)*af_2enf + (af_nbenf >=3 )*af_3enf
    return 4 * af  # annualisé
    

def _af_cong_naiss(age, _P, _option={'age': ENFS}):
    return 0

def _af_cong_jeun_trav(age, _P, _option={'age': ENFS}):
#    Les salariés de moins de 18 ans du régime non agricole bénéficient de 
#    2 jours de congés par mois et au maximum 24 jours ouvrables, 
#    l'employeur se fera rembourser par la CNSS 12 jours de congés. Les 
#    salariés âgés de 18 à 20 ans bénéficient de 18 jours de congés 
#    ouvrables par an soit 6 jours remboursés à l'employeur par la CNSS.
#    Le remboursement à l'employeur est effectué par la Caisse Nationale 
#    de Sécurité Sociale de l'avance faite en exécution de l'article 113 
#    alinéa 2 du Code du Travail.
    return 0

    
def _contr_creche(sal, agem, _P, _option={'agem': ENFS, 'sal': [CHEF, PART]}):
    '''
    Contribution aux frais de crêche
    'fam'
    '''
    # Une prise en charge peut être accordée à la mère exerçant une 
    # activité salariée et dont le salaire ne dépasse pas deux fois et demie 
    # le SMIG pour 48 heures de travail par semaine. Cette contribution est 
    # versée pour les enfants ouvrant droit aux prestations familiales et 
    # dont l'âge est compris entre 2 et 36 mois. Elle s'élève à 15 dinars par 
    # enfant et par mois pendant 11 mois.
    smig48 = _P.cotsoc.gen.smig_48h
    P = _P.pfam.creche
    elig_age = (agem <= P.age_max)*(agem >= P.age_min) 
    elig_sal = sal < P.plaf*smig48 
    return P.montant*elig_age*elig_sal*min_(P.duree,12-agem)




def _pfam(af, maj_sal_uniq, contr_creche):  # , _af_cong_naiss, af_cong_jeun_trav
    '''
    Prestations familiales
    'fam'
    '''
    return af + maj_sal_uniq + contr_creche

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


