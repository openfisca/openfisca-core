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
    AB = table.get('f2ab', 'foy', 'vous', 'declar')
    TA = table.get('f8ta', 'foy', 'vous', 'declar')
    TB = table.get('f8tb', 'foy', 'vous', 'declar')

    TF = table.get('f8tf', 'foy', 'vous', 'declar')
    TG = table.get('f8tg', 'foy', 'vous', 'declar')
    TH = table.get('f8th', 'foy', 'vous', 'declar')
    
    if self.year == 2002:

        TC = table.get('f8tc', 'foy', 'vous', 'declar')
        TD = table.get('f8td', 'foy', 'vous', 'declar')
        TE = table.get('f8te', 'foy', 'vous', 'declar')
        
        return (AB + TA + TB + TC + TD + TE - TF + TG + TH)

    elif self.year == 2003:
        TC = table.get('f8tc', 'foy', 'vous', 'declar')
        TD = table.get('f8td', 'foy', 'vous', 'declar')
        TE = table.get('f8te', 'foy', 'vous', 'declar')
        TO = table.get('f8to', 'foy', 'vous', 'declar')
        TP = table.get('f8tp', 'foy', 'vous', 'declar')
        return (AB + TA + TB + TC + TD + TE - TF + TG 
                   + TH + TO - TP)

    elif self.year == 2004:
        TC = table.get('f8tc', 'foy', 'vous', 'declar')
        TD = table.get('f8td', 'foy', 'vous', 'declar')
        TE = table.get('f8te', 'foy', 'vous', 'declar')
        TO = table.get('f8to', 'foy', 'vous', 'declar')
        TP = table.get('f8tp', 'foy', 'vous', 'declar')
        UZ = table.get('f8uz', 'foy', 'vous', 'declar')
        TZ = table.get('f8tz', 'foy', 'vous', 'declar')
        return (AB + TA + TB + TC + TD + TE - TF + TG 
                   + TH + TO - TP + UZ + TZ)
        
    elif self.year == 2005:
        
        TC = table.get('f8tc', 'foy', 'vous', 'declar')
        TD = table.get('f8td', 'foy', 'vous', 'declar')
        TE = table.get('f8te', 'foy', 'vous', 'declar')
        TO = table.get('f8to', 'foy', 'vous', 'declar')
        TP = table.get('f8tp', 'foy', 'vous', 'declar')
        UZ = table.get('f8uz', 'foy', 'vous', 'declar')
        TZ = table.get('f8tz', 'foy', 'vous', 'declar')
        WA = table.get('f8wa', 'foy', 'vous', 'declar')
        WB = table.get('f8wb', 'foy', 'vous', 'declar')
        WC = table.get('f8wc', 'foy', 'vous', 'declar')
        WE = table.get('f8we', 'foy', 'vous', 'declar')
        return (AB + TA + TB + TC + TD + TE - TF + TG 
                   + TH + TO - TP + UZ + TZ + WA + WB 
                   + WC + WE)

    elif self.year == 2006:
        
        TC = table.get('f8tc', 'foy', 'vous', 'declar')
        TE = table.get('f8te', 'foy', 'vous', 'declar')
        TO = table.get('f8to', 'foy', 'vous', 'declar')
        TP = table.get('f8tp', 'foy', 'vous', 'declar')
        UZ = table.get('f8uz', 'foy', 'vous', 'declar')
        TZ = table.get('f8tz', 'foy', 'vous', 'declar')
        WA = table.get('f8wa', 'foy', 'vous', 'declar')
        WB = table.get('f8wb', 'foy', 'vous', 'declar')
        WC = table.get('f8wc', 'foy', 'vous', 'declar')
        WD = table.get('f8wd', 'foy', 'vous', 'declar')
        WE = table.get('f8we', 'foy', 'vous', 'declar')
        WR = table.get('f8wr', 'foy', 'vous', 'declar')
        WS = table.get('f8ws', 'foy', 'vous', 'declar')
        WT = table.get('f8wt', 'foy', 'vous', 'declar')
        WU = table.get('f8wu', 'foy', 'vous', 'declar')
        return (AB + TA + TB + TC + TE - TF + TG + TH 
                   + TO - TP + UZ + TZ + WA + WB + WC 
                   + WD + WE + WR + WS + WT + WU)


    elif self.year == 2007:

        TC = table.get('f8tc', 'foy', 'vous', 'declar')
        TE = table.get('f8te', 'foy', 'vous', 'declar')
        TO = table.get('f8to', 'foy', 'vous', 'declar')
        TP = table.get('f8tp', 'foy', 'vous', 'declar')
        UZ = table.get('f8uz', 'foy', 'vous', 'declar')
        TZ = table.get('f8tz', 'foy', 'vous', 'declar')
        WA = table.get('f8wa', 'foy', 'vous', 'declar')
        WB = table.get('f8wb', 'foy', 'vous', 'declar')
        WC = table.get('f8wc', 'foy', 'vous', 'declar')
        WD = table.get('f8wd', 'foy', 'vous', 'declar')
        WR = table.get('f8wr', 'foy', 'vous', 'declar')
        WS = table.get('f8ws', 'foy', 'vous', 'declar')
        WT = table.get('f8wt', 'foy', 'vous', 'declar')
        WU = table.get('f8wu', 'foy', 'vous', 'declar')
        WV = table.get('f8wv', 'foy', 'vous', 'declar')
        WX = table.get('f8wx', 'foy', 'vous', 'declar')
        return (AB + TA + TB + TC + TE - TF + TG + TH 
                   + TO - TP + UZ + TZ + WA + WB + WC 
                   + WD + WR + WS + WT + WU + WV + WX)
        
    elif self.year == 2008:
        TC = table.get('f8tc', 'foy', 'vous', 'declar')
        TE = table.get('f8te', 'foy', 'vous', 'declar')
        TO = table.get('f8to', 'foy', 'vous', 'declar')
        TP = table.get('f8tp', 'foy', 'vous', 'declar')
        UZ = table.get('f8uz', 'foy', 'vous', 'declar')
        TZ = table.get('f8tz', 'foy', 'vous', 'declar')
        WA = table.get('f8wa', 'foy', 'vous', 'declar')
        WB = table.get('f8wb', 'foy', 'vous', 'declar')
        WC = table.get('f8wc', 'foy', 'vous', 'declar')
        WD = table.get('f8wd', 'foy', 'vous', 'declar')
        WE = table.get('f8we', 'foy', 'vous', 'declar')
        WR = table.get('f8wr', 'foy', 'vous', 'declar')
        WS = table.get('f8ws', 'foy', 'vous', 'declar')
        WT = table.get('f8wt', 'foy', 'vous', 'declar')
        WU = table.get('f8wu', 'foy', 'vous', 'declar')
        WV = table.get('f8wv', 'foy', 'vous', 'declar')
        WX = table.get('f8wx', 'foy', 'vous', 'declar')
        return (AB + TA + TB + TC + TE - TF + TG + TH 
                   + TO - TP + UZ + TZ + WA + WB + WC 
                   + WD + WE + WR + WS + WT + WU + WV + WX)

    elif self.year == 2009:
        TO = table.get('f8to', 'foy', 'vous', 'declar')
        TP = table.get('f8tp', 'foy', 'vous', 'declar')
        UZ = table.get('f8uz', 'foy', 'vous', 'declar')
        TZ = table.get('f8tz', 'foy', 'vous', 'declar')
        WA = table.get('f8wa', 'foy', 'vous', 'declar')
        WB = table.get('f8wb', 'foy', 'vous', 'declar')
        WD = table.get('f8wd', 'foy', 'vous', 'declar')
        WE = table.get('f8we', 'foy', 'vous', 'declar')
        WR = table.get('f8wr', 'foy', 'vous', 'declar')
        WS = table.get('f8ws', 'foy', 'vous', 'declar')
        WT = table.get('f8wt', 'foy', 'vous', 'declar')
        WU = table.get('f8wu', 'foy', 'vous', 'declar')
        WV = table.get('f8wv', 'foy', 'vous', 'declar')
        WX = table.get('f8wx', 'foy', 'vous', 'declar')
        WY = table.get('f8wy', 'foy', 'vous', 'declar')
        return (AB + TA + TB - TF + TG + TH + TO - TP 
                   + UZ + TZ + WA + WB + WD + WE + WR 
                   + WS + WT + WU + WV + WX + WY)

    elif self.year == 2010:
        TC = table.get('f8te', 'foy', 'vous', 'declar')
        TE = table.get('f8te', 'foy', 'vous', 'declar')
        TO = table.get('f8to', 'foy', 'vous', 'declar')
        TP = table.get('f8tp', 'foy', 'vous', 'declar')
        UZ = table.get('f8uz', 'foy', 'vous', 'declar')
        TZ = table.get('f8tz', 'foy', 'vous', 'declar')
        WA = table.get('f8wa', 'foy', 'vous', 'declar')
        WB = table.get('f8wb', 'foy', 'vous', 'declar')
        WD = table.get('f8wd', 'foy', 'vous', 'declar')
        WE = table.get('f8we', 'foy', 'vous', 'declar')
        WR = table.get('f8wr', 'foy', 'vous', 'declar')
        WT = table.get('f8wt', 'foy', 'vous', 'declar')
        WU = table.get('f8wu', 'foy', 'vous', 'declar')
        WV = table.get('f8wv', 'foy', 'vous', 'declar')
        return (AB + TA + TB + TC + TE - TF
                   + TG + TO - TP + TH + UZ
                   + TZ + WA + WB + WD + WE
                   + WR + WT + WU + WV)

def divide(self, P, table):
    '''
    Crédit d'impôt dividendes
    '''
    
    DC = table.get('f2dc', 'foy', 'vous', 'declar')
    GR = table.get('f2gr', 'foy', 'vous', 'declar')
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
    return table.get('f2bg', 'foy', 'vous', 'declar')

def accult(self, P, table):
    '''
    Acquisition de biens culturels (case 7UO)
    '''
    return P.accult.taux*table.get('f7uo', 'foy', 'vous', 'declar')

def mecena(self, P, table):
    '''
    Mécénat d'entreprise (case 7US)
    '''
    return table.get('f7us', 'foy', 'vous', 'declar')

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
    WF = table.get('f7wf', 'foy', 'vous', 'declar')
    WH = table.get('f7wh', 'foy', 'vous', 'declar')
    WK = table.get('f7wk', 'foy', 'vous', 'declar')
    WQ = table.get('f7wq', 'foy', 'vous', 'declar')
    SB = table.get('f7sb', 'foy', 'vous', 'declar')
    SD = table.get('f7sd', 'foy', 'vous', 'declar')
    SE = table.get('f7se', 'foy', 'vous', 'declar')
    SH = table.get('f7sh', 'foy', 'vous', 'declar')
     
    n = self.nbF + self.nbJ + self.nbR + self.nbH/2
    if self.year == 2005:
        max0 = (P.quaenv.max*(1+self.marpac) + 
                P.quaenv.pac1*(n>=1) +
                P.quaenv.pac2*(n>=2) +
                P.quaenv.pac2*(max_(n-2,0)) )
                
    elif self.year >= 2006:
        max0 = P.quaenv.max*(1+self.marpac) + P.quaenv.pac1*n
    
    if self.year == 2005:
        WG = table.get('f7wg', 'foy', 'vous', 'declar')    
        max1 = max_(0, max0 - WF)
        max2 = max_(0, max1 - WG)
        return (P.quaenv.taux_wf*min_(WF, max0) +
                P.quaenv.taux_wg*min_(WG, max1) +
                P.quaenv.taux_wh*min_(WH, max2) )

    elif self.year in (2006, 2007, 2008):
        WG = table.get('f7wg', 'foy', 'vous', 'declar')    
        max1 = max_(0, max0 - WF)
        max2 = max_(0, max1 - WG)
        max3 = max_(0, max2 - WH)
        return (P.quaenv.taux_wf*min_(WF, max0) +
                P.quaenv.taux_wg*min_(WG, max1) +
                P.quaenv.taux_wh*min_(WH, max2) +
                P.quaenv.taux_wq*min_(WQ, max3) )

    elif self.year == 2009:
        WG = table.get('f7wg', 'foy', 'vous', 'declar')
        SC = table.get('f7sc', 'foy', 'vous', 'declar')
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
    WI = table.get('f7wf', 'foy', 'vous', 'declar')
    WJ = table.get('f7wj', 'foy', 'vous', 'declar')
    WL = table.get('f7wl', 'foy', 'vous', 'declar')
    SF = table.get('f7sf', 'foy', 'vous', 'declar')
    
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
        UP = table.get('f7up', 'foy', 'vous', 'declar')
        UQ = table.get('f7uq', 'foy', 'vous', 'declar')
        return UP*P.acqgpl.mont_up + UQ*P.acqgpl.mont_uq

def drbail(self, P, table):
    '''
    Crédit d’impôt représentatif de la taxe additionnelle au droit de bail (case 4TQ)
    '''
    return P.drbail.taux*table.get('f4tq', 'foy', 'vous', 'declar')

def garext(self, P, table):
    '''
    Frais de garde des enfants à l’extérieur du domicile (cases 7GA à 7GC et 7GE à 7GG)
    '''
    max1 = P.garext.max
    GA = table.get('f4ga', 'foy', 'vous', 'declar')
    GB = table.get('f4gb', 'foy', 'vous', 'declar')
    GC = table.get('f4gc', 'foy', 'vous', 'declar')
    GE = table.get('f4ge', 'foy', 'vous', 'declar')
    GF = table.get('f4gf', 'foy', 'vous', 'declar')
    GG = table.get('f4gg', 'foy', 'vous', 'declar')
    
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
    UK = table.get('f7uk', 'foy', 'vous', 'declar')
    VO = table.get('f7vo', 'foy', 'vous', 'declar')
    TD = table.get('f7td', 'foy', 'vous', 'declar')
    
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
    
    DG = table.get('f7dg', 'foy', 'vous', 'declar')
    isinvalid = DG
    DL = table.get('f7dl', 'foy', 'vous', 'declar')
    DB = table.get('f7db', 'foy', 'vous', 'declar')  # dépense pour crédit d'impôt
    
    if self.year in (2007,2008):
        nbpacmin = self.nbF + self.nbH/2 + self.nbJ + self.nbN + DL
        maxBase = P.saldom.max1
        maxDuMaxNonInv = P.saldom.max2
        maxNonInv = min_(maxBase + P.saldom.pac*nbpacmin, maxDuMaxNonInv)
        maxEffectif = maxNonInv*not_(isinvalid) + P.saldom.max3*isinvalid
        
    elif self.year in (2009, 2010):
        DQ = table.get('f7dq', 'foy', 'vous', 'declar')  # 1èere année
        annee1 = DQ
        nbpacmin = self.nbF + self.nbH/2 + self.nbJ + self.nbN + DL
        maxBase = P.saldom.max1*not_(annee1) + P.saldom.max1_1ereAnnee*annee1
        maxDuMaxNonInv = P.saldom.max2*not_(annee1) + P.saldom.max2_1ereAnnee*annee1
        maxNonInv = min_(maxBase + P.saldom.pac*nbpacmin, maxDuMaxNonInv)
        maxEffectif = maxNonInv*not_(isinvalid) + P.saldom.max3*isinvalid
        
        
        
    '''
   
    DL = table.get('f7dl', 'foy', 'vous', 'declar')
    DQ = table.get('f7dq', 'foy', 'vous', 'declar')
    DB = table.get('f7db', 'foy', 'vous', 'declar')
    DG = table.get('f7dg', 'foy', 'vous', 'declar')

    
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
        DL = table.get('f7dl', 'foy', 'vous', 'declar')
        DB = table.get('f7db', 'foy', 'vous', 'declar')  # Crédit d'impôt
        nbpacmin = self.nbF + self.nbH/2 + self.nbJ + self.nbN + DL
        maxBase = P.saldom.max1
        maxDuMaxNonInv = P.saldom.max2
        maxNonInv = min_(maxBase + P.saldom.pac*nbpacmin, maxDuMaxNonInv)
        maxEffectif = maxNonInv*not_(isinvalid) + P.saldom.max3*isinvalid
        max1 = maxEffectif - min_(DB, maxEffectif)
            
    elif self.year in (2009, 2010):
        DL = table.get('f7dl', 'foy', 'vous', 'declar')  # 
        DQ = table.get('f7dq', 'foy', 'vous', 'declar')  # 1èere année
        DB = table.get('f7db', 'foy', 'vous', 'declar')  # Crédit d'impôt
        
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
    VW = table.get('f7vw', 'foy', 'vous', 'declar')
    VX = table.get('f7vx', 'foy', 'vous', 'declar')
    VY = table.get('f7vy', 'foy', 'vous', 'declar')
    VZ = table.get('f7vz', 'foy', 'vous', 'declar')
    
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
    return P.assloy.taux*table.get('f4bf', 'foy', 'vous', 'declar')

def autent(self, P, table):
    '''
    Auto-entrepreneur : versements d’impôt sur le revenu (case 8UY)
    '''
    return zeros(self.taille)

def aidmob(self, P, table):
    # crédit d'impôt aide à la mobilité
    AR = table.get('f1ar', 'foy', 'vous', 'declar')
    BR = table.get('f1br', 'foy', 'vous', 'declar')
    CR = table.get('f1cr', 'foy', 'vous', 'declar')
    DR = table.get('f1dr', 'foy', 'vous', 'declar')
    ER = table.get('f1er', 'foy', 'vous', 'declar')
    return (AR + BR + CR + DR + ER)*P.aidmob.montant

def jeunes(self, P, table):
    # crédit d'impôt en faveur des jeunes
    return  zeros(self.taille) # D'après  le document num. 2041 GY
                                # somme calculée sur formulaire 2041;
