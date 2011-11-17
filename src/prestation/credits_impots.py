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
from numpy import minimum as min_, maximum as max_, logical_not as not_, zeros

def niches(year):
    niches = []
    if year == 2002:
        niches = [creimp, accult, prlire, aidper, acqgpl, drbail]
    elif year == 2003:
        niches = [creimp, accult, mecena, prlire, aidper, acqgpl, drbail]
    elif year == 2004:
        niches = [creimp, accult, mecena, prlire, aidper, acqgpl, drbail]
    elif year == 2005:
        niches = [creimp, divide, direpa, accult, mecena, prlire, aidper,
                  quaenv, acqgpl, drbail, garext, preetu, assloy, aidmob, jeunes]
    elif year == 2006:
        niches = [creimp, divide, direpa, accult, mecena, prlire, aidper,
                  quaenv, acqgpl, drbail, garext, preetu, assloy, aidmob, jeunes]
    elif year == 2007:
        niches = [creimp, divide, direpa, accult, mecena, prlire, aidper,
                  quaenv, acqgpl, drbail, garext, preetu, saldom, inthab, assloy, 
                  aidmob, jeunes]
    elif year == 2008:
        niches = [creimp, divide, direpa, accult, mecena, prlire, aidper,
                  quaenv, drbail, garext, preetu, saldom, inthab, assloy, aidmob, 
                  jeunes]
    elif year == 2009:
        niches = [creimp, divide, direpa, accult, mecena, prlire, aidper,
                  quaenv, drbail, garext, preetu, saldom, inthab, assloy, autent]
    elif year == 2010:
        niches = [creimp, accult, percvm, direpa, mecena, prlire, aidper,
                  quaenv, drbail, garext, preetu, saldom, inthab, assloy, 
                  autent]
    return niches

def creimp(self, P, table):
    '''
    Avoir fiscaux et crédits d'impôt
    '''
    AB = table.get('vous', 'f2ab', 'foy', 'foyer')
    TA = table.get('vous', 'f8ta', 'foy', 'foyer')
    TB = table.get('vous', 'f8tb', 'foy', 'foyer')

    TF = table.get('vous', 'f8tf', 'foy', 'foyer')
    TG = table.get('vous', 'f8tg', 'foy', 'foyer')
    TH = table.get('vous', 'f8th', 'foy', 'foyer')
    
    if self.year == 2002:

        TC = table.get('vous', 'f8tc', 'foy', 'foyer')
        TD = table.get('vous', 'f8td', 'foy', 'foyer')
        TE = table.get('vous', 'f8te', 'foy', 'foyer')
        
        return (AB + TA + TB + TC + TD + TE - TF + TG + TH)

    elif self.year == 2003:
        TC = table.get('vous', 'f8tc', 'foy', 'foyer')
        TD = table.get('vous', 'f8td', 'foy', 'foyer')
        TE = table.get('vous', 'f8te', 'foy', 'foyer')
        TO = table.get('vous', 'f8to', 'foy', 'foyer')
        TP = table.get('vous', 'f8tp', 'foy', 'foyer')
        return (AB + TA + TB + TC + TD + TE - TF + TG 
                   + TH + TO - TP)

    elif self.year == 2004:
        TC = table.get('vous', 'f8tc', 'foy', 'foyer')
        TD = table.get('vous', 'f8td', 'foy', 'foyer')
        TE = table.get('vous', 'f8te', 'foy', 'foyer')
        TO = table.get('vous', 'f8to', 'foy', 'foyer')
        TP = table.get('vous', 'f8tp', 'foy', 'foyer')
        UZ = table.get('vous', 'f8uz', 'foy', 'foyer')
        TZ = table.get('vous', 'f8tz', 'foy', 'foyer')
        return (AB + TA + TB + TC + TD + TE - TF + TG 
                   + TH + TO - TP + UZ + TZ)
        
    elif self.year == 2005:
        
        TC = table.get('vous', 'f8tc', 'foy', 'foyer')
        TD = table.get('vous', 'f8td', 'foy', 'foyer')
        TE = table.get('vous', 'f8te', 'foy', 'foyer')
        TO = table.get('vous', 'f8to', 'foy', 'foyer')
        TP = table.get('vous', 'f8tp', 'foy', 'foyer')
        UZ = table.get('vous', 'f8uz', 'foy', 'foyer')
        TZ = table.get('vous', 'f8tz', 'foy', 'foyer')
        WA = table.get('vous', 'f8wa', 'foy', 'foyer')
        WB = table.get('vous', 'f8wb', 'foy', 'foyer')
        WC = table.get('vous', 'f8wc', 'foy', 'foyer')
        WE = table.get('vous', 'f8we', 'foy', 'foyer')
        return (AB + TA + TB + TC + TD + TE - TF + TG 
                   + TH + TO - TP + UZ + TZ + WA + WB 
                   + WC + WE)

    elif self.year == 2006:
        
        TC = table.get('vous', 'f8tc', 'foy', 'foyer')
        TE = table.get('vous', 'f8te', 'foy', 'foyer')
        TO = table.get('vous', 'f8to', 'foy', 'foyer')
        TP = table.get('vous', 'f8tp', 'foy', 'foyer')
        UZ = table.get('vous', 'f8uz', 'foy', 'foyer')
        TZ = table.get('vous', 'f8tz', 'foy', 'foyer')
        WA = table.get('vous', 'f8wa', 'foy', 'foyer')
        WB = table.get('vous', 'f8wb', 'foy', 'foyer')
        WC = table.get('vous', 'f8wc', 'foy', 'foyer')
        WD = table.get('vous', 'f8wd', 'foy', 'foyer')
        WE = table.get('vous', 'f8we', 'foy', 'foyer')
        WR = table.get('vous', 'f8wr', 'foy', 'foyer')
        WS = table.get('vous', 'f8ws', 'foy', 'foyer')
        WT = table.get('vous', 'f8wt', 'foy', 'foyer')
        WU = table.get('vous', 'f8wu', 'foy', 'foyer')
        return (AB + TA + TB + TC + TE - TF + TG + TH 
                   + TO - TP + UZ + TZ + WA + WB + WC 
                   + WD + WE + WR + WS + WT + WU)


    elif self.year == 2007:

        TC = table.get('vous', 'f8tc', 'foy', 'foyer')
        TE = table.get('vous', 'f8te', 'foy', 'foyer')
        TO = table.get('vous', 'f8to', 'foy', 'foyer')
        TP = table.get('vous', 'f8tp', 'foy', 'foyer')
        UZ = table.get('vous', 'f8uz', 'foy', 'foyer')
        TZ = table.get('vous', 'f8tz', 'foy', 'foyer')
        WA = table.get('vous', 'f8wa', 'foy', 'foyer')
        WB = table.get('vous', 'f8wb', 'foy', 'foyer')
        WC = table.get('vous', 'f8wc', 'foy', 'foyer')
        WD = table.get('vous', 'f8wd', 'foy', 'foyer')
        WR = table.get('vous', 'f8wr', 'foy', 'foyer')
        WS = table.get('vous', 'f8ws', 'foy', 'foyer')
        WT = table.get('vous', 'f8wt', 'foy', 'foyer')
        WU = table.get('vous', 'f8wu', 'foy', 'foyer')
        WV = table.get('vous', 'f8wv', 'foy', 'foyer')
        WX = table.get('vous', 'f8wx', 'foy', 'foyer')
        return (AB + TA + TB + TC + TE - TF + TG + TH 
                   + TO - TP + UZ + TZ + WA + WB + WC 
                   + WD + WR + WS + WT + WU + WV + WX)
        
    elif self.year == 2008:
        TC = table.get('vous', 'f8tc', 'foy', 'foyer')
        TE = table.get('vous', 'f8te', 'foy', 'foyer')
        TO = table.get('vous', 'f8to', 'foy', 'foyer')
        TP = table.get('vous', 'f8tp', 'foy', 'foyer')
        UZ = table.get('vous', 'f8uz', 'foy', 'foyer')
        TZ = table.get('vous', 'f8tz', 'foy', 'foyer')
        WA = table.get('vous', 'f8wa', 'foy', 'foyer')
        WB = table.get('vous', 'f8wb', 'foy', 'foyer')
        WC = table.get('vous', 'f8wc', 'foy', 'foyer')
        WD = table.get('vous', 'f8wd', 'foy', 'foyer')
        WE = table.get('vous', 'f8we', 'foy', 'foyer')
        WR = table.get('vous', 'f8wr', 'foy', 'foyer')
        WS = table.get('vous', 'f8ws', 'foy', 'foyer')
        WT = table.get('vous', 'f8wt', 'foy', 'foyer')
        WU = table.get('vous', 'f8wu', 'foy', 'foyer')
        WV = table.get('vous', 'f8wv', 'foy', 'foyer')
        WX = table.get('vous', 'f8wx', 'foy', 'foyer')
        return (AB + TA + TB + TC + TE - TF + TG + TH 
                   + TO - TP + UZ + TZ + WA + WB + WC 
                   + WD + WE + WR + WS + WT + WU + WV + WX)

    elif self.year == 2009:
        TO = table.get('vous', 'f8to', 'foy', 'foyer')
        TP = table.get('vous', 'f8tp', 'foy', 'foyer')
        UZ = table.get('vous', 'f8uz', 'foy', 'foyer')
        TZ = table.get('vous', 'f8tz', 'foy', 'foyer')
        WA = table.get('vous', 'f8wa', 'foy', 'foyer')
        WB = table.get('vous', 'f8wb', 'foy', 'foyer')
        WD = table.get('vous', 'f8wd', 'foy', 'foyer')
        WE = table.get('vous', 'f8we', 'foy', 'foyer')
        WR = table.get('vous', 'f8wr', 'foy', 'foyer')
        WS = table.get('vous', 'f8ws', 'foy', 'foyer')
        WT = table.get('vous', 'f8wt', 'foy', 'foyer')
        WU = table.get('vous', 'f8wu', 'foy', 'foyer')
        WV = table.get('vous', 'f8wv', 'foy', 'foyer')
        WX = table.get('vous', 'f8wx', 'foy', 'foyer')
        WY = table.get('vous', 'f8wy', 'foy', 'foyer')
        return (AB + TA + TB - TF + TG + TH + TO - TP 
                   + UZ + TZ + WA + WB + WD + WE + WR 
                   + WS + WT + WU + WV + WX + WY)

    elif self.year == 2010:
        TC = table.get('vous', 'f8te', 'foy', 'foyer')
        TE = table.get('vous', 'f8te', 'foy', 'foyer')
        TO = table.get('vous', 'f8to', 'foy', 'foyer')
        TP = table.get('vous', 'f8tp', 'foy', 'foyer')
        UZ = table.get('vous', 'f8uz', 'foy', 'foyer')
        TZ = table.get('vous', 'f8tz', 'foy', 'foyer')
        WA = table.get('vous', 'f8wa', 'foy', 'foyer')
        WB = table.get('vous', 'f8wb', 'foy', 'foyer')
        WD = table.get('vous', 'f8wd', 'foy', 'foyer')
        WE = table.get('vous', 'f8we', 'foy', 'foyer')
        WR = table.get('vous', 'f8wr', 'foy', 'foyer')
        WT = table.get('vous', 'f8wt', 'foy', 'foyer')
        WU = table.get('vous', 'f8wu', 'foy', 'foyer')
        WV = table.get('vous', 'f8wv', 'foy', 'foyer')
        return (AB + TA + TB + TC + TE - TF
                   + TG + TO - TP + TH + UZ
                   + TZ + WA + WB + WD + WE
                   + WR + WT + WU + WV)

def divide(self, P, table):
    '''
    Crédit d'impôt dividendes
    '''
    
    DC = table.get('vous', 'f2dc', 'foy', 'foyer')
    GR = table.get('vous', 'f2gr', 'foy', 'foyer')
    max1 = P.divide.max*(self.marpac+1)
    return min_(P.divide.taux*(DC + GR), max1)

def percvm(self, P, table):
    '''
    Crédit d’impôt pertes sur cessions de valeurs mobilières (3W)
    '''
    return zeros(self.taille)

def direpa(self, P, table):
    '''
    Crédit d’impôt directive « épargne » (case 2BG)
    '''
    return table.get('vous', 'f2bg', 'foy', 'foyer')

def accult(self, P, table):
    '''
    Acquisition de biens culturels (case 7UO)
    '''
    return P.accult.taux*table.get('vous', 'f7uo', 'foy', 'foyer')

def mecena(self, P, table):
    '''
    Mécénat d'entreprise (case 7US)
    '''
    return table.get('vous', 'f7us', 'foy', 'foyer')

def prlire(self, P, table):
    '''
    Prélèvement libératoire à restituer (case 2DH)
    '''
    return zeros(self.taille)

def quaenv(self, P, table):
    '''
    Crédits d’impôt pour dépenses en faveur de la qualité environnementale 
    (cases 7WF, 7WH, 7WK, 7WQ, 7SB, 7SD, 7SE et 7SH)
    '''
    WF = table.get('vous', 'f7wf', 'foy', 'foyer')
    WH = table.get('vous', 'f7wh', 'foy', 'foyer')
    WK = table.get('vous', 'f7wk', 'foy', 'foyer')
    WQ = table.get('vous', 'f7wq', 'foy', 'foyer')
    SB = table.get('vous', 'f7sb', 'foy', 'foyer')
    SD = table.get('vous', 'f7sd', 'foy', 'foyer')
    SE = table.get('vous', 'f7se', 'foy', 'foyer')
    SH = table.get('vous', 'f7sh', 'foy', 'foyer')
     
    n = self.nbF + self.nbJ + self.nbR + self.nbH/2
    if self.year == 2005:
        max0 = (P.quaenv.max*(1+self.marpac) + 
                P.quaenv.pac1*(n>=1) +
                P.quaenv.pac2*(n>=2) +
                P.quaenv.pac2*(max_(n-2,0)) )
                
    elif self.year >= 2006:
        max0 = P.quaenv.max*(1+self.marpac) + P.quaenv.pac1*n
    
    if self.year == 2005:
        WG = table.get('vous', 'f7wg', 'foy', 'foyer')    
        max1 = max_(0, max0 - WF)
        max2 = max_(0, max1 - WG)
        return (P.quaenv.taux_wf*min_(WF, max0) +
                P.quaenv.taux_wg*min_(WG, max1) +
                P.quaenv.taux_wh*min_(WH, max2) )

    elif self.year in (2006, 2007, 2008):
        WG = table.get('vous', 'f7wg', 'foy', 'foyer')    
        max1 = max_(0, max0 - WF)
        max2 = max_(0, max1 - WG)
        max3 = max_(0, max2 - WH)
        return (P.quaenv.taux_wf*min_(WF, max0) +
                P.quaenv.taux_wg*min_(WG, max1) +
                P.quaenv.taux_wh*min_(WH, max2) +
                P.quaenv.taux_wq*min_(WQ, max3) )

    elif self.year == 2009:
        WG = table.get('vous', 'f7wg', 'foy', 'foyer')
        SC = table.get('vous', 'f7sc', 'foy', 'foyer')
        max1 = max_(0, max0 - WF)
        max2 = max_(0, max1 - SE)
        max3 = max_(0, max2 - WK)
        max4 = max_(0, max3 - SD)
        max5 = max_(0, max4 - WG)
        max6 = max_(0, max5 - SC)
        max7 = max_(0, max6 - WH)
        return (P.quaenv.taux_wf*min_(WF, max0) +
                P.quaenv.taux_se*min_(SE, max1) +
                P.quaenv.taux_wk*min_(WK, max2) +
                P.quaenv.taux_sd*min_(SD, max3) +
                P.quaenv.taux_wg*min_(WG, max4) +
                P.quaenv.taux_sc*min_(SC, max5) +
                P.quaenv.taux_wh*min_(WH, max6) +
                P.quaenv.taux_sb*min_(SB, max7) )

    elif self.year == 2010:
        max1 = max_(0, max0 - WF)
        max2 = max_(0, max1 - SE)
        max3 = max_(0, max2 - WK)
        max4 = max_(0, max3 - SD)
        max5 = max_(0, max4 - WH)
        max6 = max_(0, max5 - SB)
        max7 = max_(0, max6 - WQ)
        return (P.quaenv.taux_wf*min_(WF, max0) +
                P.quaenv.taux_se*min_(SE, max1) +
                P.quaenv.taux_wk*min_(WK, max2) +
                P.quaenv.taux_sd*min_(SD, max3) +
                P.quaenv.taux_wh*min_(WH, max4)+
                P.quaenv.taux_sb*min_(SB, max5) +
                P.quaenv.taux_wq*min_(WQ, max6) +
                P.quaenv.taux_sh*min_(SH, max7) )

def aidper(self, P, table):
    '''
    Crédits d’impôt pour dépenses en faveur de l’aide aux personnes 
    (cases 7WI, 7WJ, 7WL et 7SF).
    '''
    WI = table.get('vous', 'f7wf', 'foy', 'foyer')
    WJ = table.get('vous', 'f7wj', 'foy', 'foyer')
    WL = table.get('vous', 'f7wl', 'foy', 'foyer')
    SF = table.get('vous', 'f7sf', 'foy', 'foyer')
    
    n = self.nbF + self.nbJ + self.nbR + self.nbH/2
    if self.year <= 2005:
        max0 = (P.aidper.max*(1+self.marpac) + 
                P.aidper.pac1*(n>=1) +
                P.aidper.pac2*(n>=2) +
                P.aidper.pac2*(max_(n-2,0)) )
               
    elif self.year >= 2006:
        max0 = P.aidper.max*(1+self.marpac) + P.aidper.pac1*n

    if self.year in (2002,2003):
        return P.aidper.taux_wi*min_(WI, max0) # TODO enfant en résidence altérnée
    elif self.year <= 2009:
        max1 = max_(0, max0 - WJ)
        return (P.aidper.taux_wj*min_(WJ, max0) +
                P.aidper.taux_wi*min_(WI, max1) )
    elif self.year == 2010:
        max1 = max_(0, max0 - WL)
        max2 = max_(0, max1 - SF)
        max3 = max_(0, max2 - WJ)
        return (P.aidper.taux_wl*min_(WL, max0) +
                P.aidper.taux_sf*min_(SF, max1) +
                P.aidper.taux_wj*min_(WJ, max2) +
                P.aidper.taux_wi*min_(WI, max3) )

def acqgpl(self, P, table):
    # crédit d'impôt pour dépense d'acquisition ou de transformation d'un véhicule GPL ou mixte
    if 2002 <= self.year <= 2007:
        UP = table.get('vous', 'f7up', 'foy', 'foyer')
        UQ = table.get('vous', 'f7uq', 'foy', 'foyer')
        return UP*P.acqgpl.mont_up + UQ*P.acqgpl.mont_uq

def drbail(self, P, table):
    '''
    Crédit d’impôt représentatif de la taxe additionnelle au droit de bail (case 4TQ)
    '''
    return P.drbail.taux*table.get('vous', 'f4tq', 'foy', 'foyer')

def garext(self, P, table):
    '''
    Frais de garde des enfants à l’extérieur du domicile (cases 7GA à 7GC et 7GE à 7GG)
    '''
    max1 = P.garext.max
    GA = table.get('vous', 'f4ga', 'foy', 'foyer')
    GB = table.get('vous', 'f4gb', 'foy', 'foyer')
    GC = table.get('vous', 'f4gc', 'foy', 'foyer')
    GE = table.get('vous', 'f4ge', 'foy', 'foyer')
    GF = table.get('vous', 'f4gf', 'foy', 'foyer')
    GG = table.get('vous', 'f4gg', 'foy', 'foyer')
    
    return P.garext.taux*(min_(GA, max1) + 
                          min_(GB, max1) +
                          min_(GC, max1) +
                          min_(GE, max1/2) +
                          min_(GF, max1/2) +
                          min_(GG, max1/2))
def preetu(self, P, table):
    '''
    Crédit d’impôt pour souscription de prêts étudiants (cases 7UK, 7VO et 7TD)
    '''
    UK = table.get('vous', 'f7uk', 'foy', 'foyer')
    VO = table.get('vous', 'f7vo', 'foy', 'foyer')
    TD = table.get('vous', 'f7td', 'foy', 'foyer')
    
    if self.year == 2005: 
        max1 = P.preetu.max
    elif self.year >= 2006:
        max1 = P.preetu.max*(1+VO)
    if self.year in (2005,2006,2007):
        return P.preetu.taux*min_(UK, max1)
    elif self.year >=2008:
        return P.preetu.taux*min_(UK, P.preetu.max) + P.preetu.taux*min_(TD, max1)

def saldom(self, P, table):
    '''
    Crédit d’impôt emploi d’un salarié à domicile (cases 7DB, 7DG)
    '''
    # TODO, TODO, TODO check avant 2010
    
    DG = table.get('vous', 'f7dg', 'foy', 'foyer')
    isinvalid = DG
    DL = table.get('vous', 'f7dl', 'foy', 'foyer')
    DB = table.get('vous', 'f7db', 'foy', 'foyer')  # dépense pour crédit d'impôt
    
    if self.year in (2007,2008):
        nbpacmin = self.nbF + self.nbH/2 + self.nbJ + self.nbN + DL
        maxBase = P.saldom.max1
        maxDuMaxNonInv = P.saldom.max2
        maxNonInv = min_(maxBase + P.saldom.pac*nbpacmin, maxDuMaxNonInv)
        maxEffectif = maxNonInv*not_(isinvalid) + P.saldom.max3*isinvalid
        
    elif self.year in (2009, 2010):
        DQ = table.get('vous', 'f7dq', 'foy', 'foyer')  # 1èere année
        annee1 = DQ
        nbpacmin = self.nbF + self.nbH/2 + self.nbJ + self.nbN + DL
        maxBase = P.saldom.max1*not_(annee1) + P.saldom.max1_1ereAnnee*annee1
        maxDuMaxNonInv = P.saldom.max2*not_(annee1) + P.saldom.max2_1ereAnnee*annee1
        maxNonInv = min_(maxBase + P.saldom.pac*nbpacmin, maxDuMaxNonInv)
        maxEffectif = maxNonInv*not_(isinvalid) + P.saldom.max3*isinvalid
        
        
        
    '''
   
    DL = table.get('vous', 'f7dl', 'foy', 'foyer')
    DQ = table.get('vous', 'f7dq', 'foy', 'foyer')
    DB = table.get('vous', 'f7db', 'foy', 'foyer')
    DG = table.get('vous', 'f7dg', 'foy', 'foyer')

    
    isinvalid = DG
            
    annee1 = DQ
    nbpacmin = self.nbF + self.nbH / 2 + self.nbJ + self.nbN + DL
    maxBase = P.saldom.max1 * not_(annee1) + P.saldom.max1_1ereAnnee * annee1
    maxDuMaxNonInv = P.saldom.max2 * not_(annee1) + P.saldom.max2_1ereAnnee * annee1
    maxDuMax = maxDuMaxNonInv * not_(isinvalid) + P.saldom.max3 * isinvalid
    maxEffectif = min_(maxBase + P.saldom.pac * nbpacmin, maxDuMax)
    maxEffectif = max_(maxEffectif,P.saldom.max3*isinvalid)
    '''
    
    '''
    elif self.year in (2007,2008):
        DL = table.get('vous', 'f7dl', 'foy', 'foyer')
        DB = table.get('vous', 'f7db', 'foy', 'foyer')  # Crédit d'impôt
        nbpacmin = self.nbF + self.nbH/2 + self.nbJ + self.nbN + DL
        maxBase = P.saldom.max1
        maxDuMaxNonInv = P.saldom.max2
        maxNonInv = min_(maxBase + P.saldom.pac*nbpacmin, maxDuMaxNonInv)
        maxEffectif = maxNonInv*not_(isinvalid) + P.saldom.max3*isinvalid
        max1 = maxEffectif - min_(DB, maxEffectif)
            
    elif self.year in (2009, 2010):
        DL = table.get('vous', 'f7dl', 'foy', 'foyer')  # 
        DQ = table.get('vous', 'f7dq', 'foy', 'foyer')  # 1èere année
        DB = table.get('vous', 'f7db', 'foy', 'foyer')  # Crédit d'impôt
        
        annee1 = DQ
        nbpacmin = self.nbF + self.nbH/2 + self.nbJ + self.nbN + DL
        maxBase = P.saldom.max1*not_(annee1) + P.saldom.max1_1ereAnnee*annee1
        maxDuMaxNonInv = P.saldom.max2*not_(annee1) + P.saldom.max2_1ereAnnee*annee1
        maxNonInv = min_(maxBase + P.saldom.pac*nbpacmin, maxDuMaxNonInv)
        maxEffectif = maxNonInv*not_(isinvalid) + P.saldom.max3*isinvalid
        max1 = maxEffectif - min_(DB, maxEffectif)

    
    '''
    
    return P.saldom.taux*min_(DB, maxEffectif)


def inthab(self, P, table):
    '''
    Crédit d’impôt intérêts des emprunts pour l’habitation principale (cases 7VW, 7VX, 7VY et 7VZ)
    '''
    VW = table.get('vous', 'f7vw', 'foy', 'foyer')
    VX = table.get('vous', 'f7vx', 'foy', 'foyer')
    VY = table.get('vous', 'f7vy', 'foy', 'foyer')
    VZ = table.get('vous', 'f7vz', 'foy', 'foyer')
    
    invalide = self.caseP |self.caseF | (self.nbG!=0) | (self.nbR!=0)
    nb = self.nbF + self.nbH/2 + self.nbR + self.nbJ + self.nbN
    max0 = P.inthab.max*(self.marpac+1)*(1+invalide) + nb*P.inthab.add

    if self.year == 2007:
        return zeros(self.taille)
    if self.year == 2008:  
        max1 = min_(max0 - VY, 0)
        return (P.inthab.taux1*min_(VY, max0) + 
                P.inthab.taux3*min_(VZ, max1) )
    if self.year == 2009:
        max1 = min_(max0 - VX, 0)
        max2 = min_(max1 - VY, 0)
        return (P.inthab.taux1*min_(VX, max0) + 
                P.inthab.taux1*min_(VY, max1) + 
                P.inthab.taux3*min_(VZ, max2) )
    if self.year == 2010:
        max1 = min_(max0 - VX, 0)
        max2 = min_(max1 - VY, 0)
        max3 = min_(max2 - VW, 0)
        return (P.inthab.taux1*min_(VX, max0) + 
                P.inthab.taux1*min_(VY, max1) + 
                P.inthab.taux2*min_(VW, max2) + 
                P.inthab.taux3*min_(VZ, max3) )

def assloy(self, P, table):
    '''
    Crédit d’impôt primes d’assurance pour loyers impayés (case 4BF)
    '''
    return P.assloy.taux*table.get('vous', 'f4bf', 'foy', 'foyer')

def autent(self, P, table):
    '''
    Auto-entrepreneur : versements d’impôt sur le revenu (case 8UY)
    '''
    return zeros(self.taille)

def aidmob(self, P, table):
    # crédit d'impôt aide à la mobilité
    AR = table.get('vous', 'f1ar', 'foy', 'foyer')
    BR = table.get('vous', 'f1br', 'foy', 'foyer')
    CR = table.get('vous', 'f1cr', 'foy', 'foyer')
    DR = table.get('vous', 'f1dr', 'foy', 'foyer')
    ER = table.get('vous', 'f1er', 'foy', 'foyer')
    return (AR + BR + CR + DR + ER)*P.aidmob.montant

def jeunes(self, P, table):
    # crédit d'impôt en faveur des jeunes
    return  zeros(self.taille) # D'après  le document num. 2041 GY
                                # somme calculée sur formulaire 2041;
