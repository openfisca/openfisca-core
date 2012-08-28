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
from numpy import ( maximum as max_, minimum as min_, logical_xor as xor_, 
                     logical_not as not_, round) 

from tunisie.data import QUIFOY

VOUS = QUIFOY['vous']
CONJ = QUIFOY['conj']
PAC1 = QUIFOY['pac1']
PAC2 = QUIFOY['pac2']
PAC3 = QUIFOY['pac3']
ALL = [x[1] for x in QUIFOY]
        



###############################################################################
## Initialisation de quelques variables utiles pour la suite
###############################################################################


def _nb_adult(marie, celdiv, veuf):
    return 2*marie + 1*(celdiv | veuf)

def _marie(statmarit):
    '''
    Marié (1) 
    'foy'
    '''
    return (statmarit == 1)

def _celib(statmarit):
    '''
    Célibataire 
    'foy'
    '''
    return (statmarit == 2) 

def _divor(statmarit):
    '''
    Divorcé (3)
    'foy'
    '''
    return (statmarit == 3)

def _veuf(statmarit):
    '''
    Veuf (4)
    'foy'
    '''
    return statmarit == 4



def _nb_enf():
    '''
    Nombre d'enfants
    '''
    pass

def _nb_enf_sup():
    '''
    Nombre d'enfants étudiant du supérieur non boursiers
    '''
    pass
    
def nb_infirme(): 
    '''
    Nombre d'enfants infirmes
    '''
    pass
    
def nb_par():
    pass


###############################################################################
## Revenus catégoriels
###############################################################################


def _bic():
    '''
    Bénéfices industriels et commerciaux
    ''' 
#    return bic_reel + bic_simpl + bic_forf TODO
    pass

# régime réel
# régime réel simplifié
# régime forfaitaire


def _bnc():   
    '''
    Bénéfices des professions non commerciales
    '''
    pass
     
def _beap():
    '''
    Bénéfices de l'exploitation agricole et de pêche
    '''
    pass

    
def _rvcm(capm_banq, capm_cent, capm_caut, capm_part, capm_oblig, capm_caisse, capm_plfcc, capm_epinv, capm_aut):
    '''
    Revenus de valeurs mobilières et de capitaux mobiliers
    '''
    return capm_banq + capm_cent + capm_caut + capm_part + capm_oblig + capm_caisse + capm_plfcc + capm_epinv + capm_aut
    
    
def _fon_forf_bati(fon_forf_bati_rec, fon_forf_bati_rel, fon_forf_bati_fra, fon_forf_bati_tax, _P):
    '''
    Revenus fonciers net des immeubles bâtis
    '''
    P = _P.ir.fon.abat_bat
    return max(0, fon_forf_bati_rec*(1-P) + fon_forf_bati_rel - fon_forf_bati_fra - fon_forf_bati_tax)

def _fon_forf_nbat(fon_forf_nbat_rec, fon_forf_nbat_dep, fon_forf_nbat_tax, _P):
    '''
    Revenus fonciers net des terrains non bâtis
    '''
    return max(0, fon_forf_nbat_rec - fon_forf_nbat_dep - fon_forf_nbat_tax)


def _rfon(fon_reel_fisc, fon_forf_bat, fon_forf_nbat, fon_sp):
    '''
    Revenus fonciers
    '''    
    return fon_reel_fisc + fon_forf_bat + fon_forf_nbat + fon_sp

def _sal_net(tra_sal, sal_nat, smig, _P):
    '''
    Revenu imposé comme des salaires net des abatements 
    'ind'
    '''
    P = _P.ir.tspr
    return (tra_sal + sal_nat)*(1 - P.abat_sal) - smig*P.smig 


def _pen_net(pen, pen_nat, _P):
    '''
    Pensions et rentes viagères après abattements
    'ind'
    '''
    P = _P.ir.tspr
    return (pen + pen_nat)*(1-P.abat_pen) 

def _tspr(sal_net, pen_net):
    '''
    Traitemens salaires pensions 
    'ind'
    '''
    return sal_net + pen_net
        
def _retr(etr_sal, etr_pen, etr_trans, etr_aut, _P):
    '''
    Autres revenus ie revenus de source étrangère n’ayant pas subi l’impôt dans le pays d'origine
    '''
    P = _P.ir.tspr
    return etr_sal*(1-P.abat_sal) + etr_pen*(1-P.abat_pen) + etr_trans*(1-P.abat_pen_etr) + etr_aut



###############################################################################
## Déroulé du calcul de l'irpp
###############################################################################


def _rng(tspr, rfon, retr, rvcm):
    '''
    Revenu net global  soumis à l'impôt après déduction des abattements
    'foy'
    '''
    return tspr + rfon + + rvcm + retr 

#############################  
#    Déductions
#############################

## 1/ Au titre des revenus et bénéfices provenant de l’activité

## 2/ Autres déductions


def _deduc_int(capm_banq, capm_cent, capm_oblig, _P):
    P = _P.deduc
    return  max ( max( max(capm_banq, P.banq.plaf) + max(capm_cent, P.cent.plaf), P.banq.plaf ) +  
                 max(capm_oblig, P.oblig.plaf), P.oblig.plaf) 

def _deduc_fam(rgn, chef, nb_enf, nb_enf_sup, nb_infirme, nb_par, _P):
    ''' 
    Déductions pour situation et charges de famille
    '''
    P = _P.ir.fam
    
    enf = P.chef*chef + (nb_enf >= 1)*P.enf1 + (nb_enf >= 2)*P.enf2 + (nb_enf >= 3)*P.enf3 + (nb_enf >= 4)*P.enf4   
    sup = P.enf_sup*nb_enf_sup 
    infirme =  P.infirme*nb_infirme
    parent = min(P.parent_taux*rgn, P.parent_max)
    
    return enf + sup + infirme + parent

def _rente():
    '''
    Déductions des arrérages et rentes payées à titre obligatoire et gratuit
    '''
    return 0 # TODO
    
def _ass_vie(prime_ass_vie, statmarit, nb_enf, _P):
    '''    
    Primes afférentes aux contrats d'assurance-vie collectifs ou individuels
    '''
    P = _P.ir.deduc.ass_vie
    marie = statmarit # TODO
    deduc = min(prime_ass_vie, P.plaf + marie*P.conj_plaf + nb_enf*P.enf_plaf) 
    return deduc


#     - Les remboursements des prêts universitaires en principal et en intérêts
#    - Revenus et bénéfices réinvestis dans les conditions et limites
#    prévues par la législation en vigueur dont notamment :
#     les revenus provenant de l'exportation, totalement pendant 10
#    ans à partir de la première opération d'exportation;
#     les revenus provenant de l’hébergement et de la restauration
#    des étudiants pendant dix ans ;
#     les revenus provenant du courtage international dans la limite
#    de 50% pendant 10 ans à partir de la première opération de courtage
#    international;
#     les montants déposés dans les comptes-épargne pour
#    l’investissement et dans les comptes-épargne en actions dans la
#    limite de 20.000D par an et sous réserve du minimum d’IR ;
#     la plus-value provenant des opérations de transmission des
#    entreprises en difficultés économiques ou des entreprises sous
#    forme de participations ou d’actifs pour départ du propriétaire à la
#    retraite ou pour incapacité de poursuivre la gestion et ce, sous
#    certaines conditions,
#     la plus-value provenant de l’apport d’une entreprise individuelle
#    au capital d’une société ;
#     les revenus réinvestis dans la souscription au capital des
#    entreprises dans les conditions prévues par la législation relative aux
#    incitations fiscales;
#     les revenus réinvestis dans la réalisation de projets
#    d’hébergement et de restauration universitaires sous réserve du
#    minimum d’IR.
#     Les revenus provenant de la location des terres agricoles
#    réservées aux grandes cultures objet de contrat de location conclus
#    pour une période minimale de trois ans. 


def _deduc_smig():
    '''
    Déduction supplémentaire pour les salariés payés au « SMIG » et « SMAG »
    '''
    return 0 # TODO voir avec tspr

def _rni(rgn, deduc_fam, rente, ass_vie):
    '''
    Revenu net imposable ie soumis à au barême de l'impôt après déduction des dépenses et charges professionnelles et des revenus non soumis à l'impôt
    '''
    return rgn - (deduc_fam + rente + ass_vie)
    

def _ir_brut(rni, _P):
    '''
    Impot sur le revenu avant non imposabilité
    '''
    bar = _P.ir.bareme
    bar.t_x()
    return bar.calc(rni)



