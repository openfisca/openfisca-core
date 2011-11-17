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
from numpy import minimum as min_, maximum as max_, zeros

def niches(year):
    '''
    Renvoie la liste des charges déductibles à intégrer en fonction de l'année
    '''
    if year in (2002, 2003):
        niches1 = [penali, acc75a, percap, deddiv, doment]
        niches2 = [sofipe, cinema ]
        ind_rfr = [2, 5, 6] #TODO: check
    elif year in (2004,2005):
        niches1 = [penali, acc75a, percap, deddiv, doment, eparet]
        niches2 = [sofipe, cinema ]
        ind_rfr = [2, 5, 6, 7]
    elif year == 2006:
        niches1 = [penali, acc75a, percap, deddiv, eparet]
        niches2 = [sofipe ]
        ind_rfr = [2, 4, 5]
    elif year in (2007, 2008):
        niches1 = [penali, acc75a, deddiv, eparet]
        niches2 = [ecodev]
        ind_rfr = [ 3, 4]
    elif year in (2009, 2010):
        niches1 = [penali, acc75a, deddiv, eparet, grorep]
        niches2 = []
        ind_rfr = [3]
    
    return niches1, niches2, ind_rfr

def penali(self, P, table):
    '''
    Pensions alimentaires
    '''
    GI = table.get('vous', 'f6gi', 'foy', 'foyer')
    GJ = table.get('vous', 'f6gj', 'foy', 'foyer')
    GP = table.get('vous', 'f6gp', 'foy', 'foyer')
    max1 = P.penalim.max 
    if self.year <= 2005:
        # TODO: si vous subvenez seul(e) à l'entretien d'un enfant marié ou 
        # pacsé ou chargé de famille, quel que soit le nmbre d'enfants du jeune 
        # foyer, la déduction est limitée à 2*max
        return (min_(GI ,max1) + 
                min_(GJ, max1) + 
                GP)
    else:
        taux = P.penalim.taux
        EL = table.get('vous', 'f6el', 'foy', 'foyer')
        EM = table.get('vous', 'f6em', 'foy', 'foyer')
        GU = table.get('vous', 'f6gu', 'foy', 'foyer')
        # check si c'est bien la déduction marjorée qu'il faut plafonner
        return (min_(GI*(1 + taux), max1) + 
                min_(GJ*(1 + taux), max1) + 
                min_(EL, max1) + 
                min_(EM, max1) + 
                GP*(1 + taux) + GU)

def acc75a(self, P, table):
    '''
    Frais d’accueil sous votre toit d’une personne de plus de 75 ans
    '''
    EU = table.get('vous', 'f6eu', 'foy', 'foyer')
    EV = table.get('vous', 'f6ev', 'foy', 'foyer')
    amax = P.acc75a.max*max_(1, EV)
    return min_(EU, amax)

def percap(self, P, table):
    '''
    Pertes en capital consécutives à la souscription au capital de sociétés 
    nouvelles ou de sociétés en difficulté (cases CB et DA de la déclaration 
    complémentaire)
    '''
    if self.year <= 2002:
        CB = table.get('vous', 'f6cb', 'foy', 'foyer')
        max_cb = P.percap.max_cb*(1 + self.marpac)
        return min_(CB, max_cb) 
    elif self.year <= 2006:
        max_cb = P.percap.max_cb*(1 + self.marpac)
        max_da = P.percap.max_da*(1 + self.marpac)

        CB = table.get('vous', 'f6cb', 'foy', 'foyer')
        DA = table.get('vous', 'f6da', 'foy', 'foyer')

        return min_(min_(CB, max_cb) + min_(DA,max_da), max_da)   

def deddiv(self, P, table):
    '''
    Déductions diverses (case DD)
    '''
    return table.get('vous', 'f6dd', 'foy', 'foyer')

def doment(self, P, table):
    '''
    Investissements DOM-TOM dans le cadre d’une entreprise (case EH de la 
    déclaration n° 2042 complémentaire)
    '''
    if self.year <= 2005:
        return table.get('vous', 'f6eh', 'foy', 'foyer')

def eparet(self, P, table):
    '''
    Épargne retraite - PERP, PRÉFON, COREM et CGOS
    '''
    # TODO: En théorie, les plafonds de déductions (ps, pt, pu) sont calculés sur 
    # le formulaire 2041 GX
    if self.year <= 2003:
        return None
    elif self.year <= 2010:
        PS = table.get('vous', 'f6ps', 'foy', 'foyer')
        RS = table.get('vous', 'f6rs', 'foy', 'foyer')
        SS = table.get('vous', 'f6ss', 'foy', 'foyer')
        PT = table.get('vous', 'f6ps', 'foy', 'foyer')
        RT = table.get('vous', 'f6rs', 'foy', 'foyer')
        ST = table.get('vous', 'f6ss', 'foy', 'foyer')
        PU = table.get('vous', 'f6ps', 'foy', 'foyer')
        RU = table.get('vous', 'f6rs', 'foy', 'foyer')
        SU = table.get('vous', 'f6ss', 'foy', 'foyer')
        return ((PS==0)*(RS + SS) + 
                (PS!=0)*min_(RS + SS, PS) +
                (PT==0)*(RT + ST) + 
                (PT!=0)*min_(RT + ST, PT) +
                (PU==0)*(RU + SU) + 
                (PU!=0)*min_(RU + SU, PU))

def sofipe(self, P, table):
    '''
    Souscriptions au capital des SOFIPÊCHE (case CC de la déclaration 
    complémentaire)
    '''
    if self.year <= 2006:
        CC = table.get('vous', 'f6cc', 'foy', 'foyer')
        max1 = min_(P.sofipe.taux*self.rbg_int, P.sofipe.max*(1+self.marpac))
        return min_(CC, max1)

def cinema(self, P, table):
    '''
    Souscriptions en faveur du cinéma ou de l’audiovisuel (case AA de la 
    déclaration n° 2042 complémentaire)
    '''
    if self.year <= 2005:
        AA = table.get('vous', 'f6aa', 'foy', 'foyer')
        max1 = min_(P.cinema.taux*self.rbg_int, P.cinema.max)
        return min_(AA, max1)

def ecodev(self, P, table):
    '''
    Versements sur un compte épargne codéveloppement (case EH de la déclaration 
    complémentaire)
    '''
    if self.year <= 2006:
        return None
    elif self.year <= 2008:
        EH = table.get('vous', 'f6eh', 'foy', 'foyer')
        max1 = min_(P.ecodev.taux*self.rbg_int, P.ecodev.max)
        return min_(EH, max1)

def grorep(self, P, table):
    '''
    Dépenses de grosses réparations des nus-propriétaires (case 6CB et 6HJ)
    '''
    CB = table.get('vous', 'f6cb', 'foy', 'foyer')
    HJ = table.get('vous', 'f6hj', 'foy', 'foyer')
    return min_(CB+HJ,P.grorep.max)

def charges_calc(self, P, table, niches1, niches2, ind_rfr):
    '''
    niches1 : niches avant le rbg_int
    niches2 : niches après le rbg_int
    niches3 : indices des niches à ajouter au revenu fiscal de référence
    '''
    rest = max_(0,self.rbg- self.CSGdeduc )
    tot = zeros(self.taille)
    mont = []

    for niche in niches1:
        mont.append(min_(niche(self, P, table), rest))
        rest -= mont[-1]
        tot  += mont[-1]

    self.rbg_int = rest*1 # TODO ATTENTION, astérisque pas prise en compte

    for niche in niches2:
        mont.append(min_(niche(self, P, table), rest))
        rest -= mont[-1]
        tot  += mont[-1]

    
    ## charges déduites à ajouter au revenu fiscal de référence
    self.rfr_cd = zeros(self.taille)
    for i in ind_rfr:
        self.rfr_cd += mont[i]

    ## total18
    self.CD  = tot 
