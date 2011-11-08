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
from numpy import minimum, maximum, zeros
from numpy import logical_not as lnot

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
    AB = table.getFoyer('vous', 'f2ab', 'foyer')
    TA = table.getFoyer('vous', 'f8ta', 'foyer')
    TB = table.getFoyer('vous', 'f8tb', 'foyer')

    TF = table.getFoyer('vous', 'f8tf', 'foyer')
    TG = table.getFoyer('vous', 'f8tg', 'foyer')
    TH = table.getFoyer('vous', 'f8th', 'foyer')
    
    if self.year == 2002:

        TC = table.getFoyer('vous', 'f8tc', 'foyer')
        TD = table.getFoyer('vous', 'f8td', 'foyer')
        TE = table.getFoyer('vous', 'f8te', 'foyer')
        
        return (AB + TA + TB + TC + TD + TE - TF + TG + TH)

    elif self.year == 2003:
        TC = table.getFoyer('vous', 'f8tc', 'foyer')
        TD = table.getFoyer('vous', 'f8td', 'foyer')
        TE = table.getFoyer('vous', 'f8te', 'foyer')
        TO = table.getFoyer('vous', 'f8to', 'foyer')
        TP = table.getFoyer('vous', 'f8tp', 'foyer')
        return (AB + TA + TB + TC + TD + TE - TF + TG 
                   + TH + TO - TP)

    elif self.year == 2004:
        TC = table.getFoyer('vous', 'f8tc', 'foyer')
        TD = table.getFoyer('vous', 'f8td', 'foyer')
        TE = table.getFoyer('vous', 'f8te', 'foyer')
        TO = table.getFoyer('vous', 'f8to', 'foyer')
        TP = table.getFoyer('vous', 'f8tp', 'foyer')
        UZ = table.getFoyer('vous', 'f8uz', 'foyer')
        TZ = table.getFoyer('vous', 'f8tz', 'foyer')
        return (AB + TA + TB + TC + TD + TE - TF + TG 
                   + TH + TO - TP + UZ + TZ)
        
    elif self.year == 2005:
        
        TC = table.getFoyer('vous', 'f8tc', 'foyer')
        TD = table.getFoyer('vous', 'f8td', 'foyer')
        TE = table.getFoyer('vous', 'f8te', 'foyer')
        TO = table.getFoyer('vous', 'f8to', 'foyer')
        TP = table.getFoyer('vous', 'f8tp', 'foyer')
        UZ = table.getFoyer('vous', 'f8uz', 'foyer')
        TZ = table.getFoyer('vous', 'f8tz', 'foyer')
        WA = table.getFoyer('vous', 'f8wa', 'foyer')
        WB = table.getFoyer('vous', 'f8wb', 'foyer')
        WC = table.getFoyer('vous', 'f8wc', 'foyer')
        WE = table.getFoyer('vous', 'f8we', 'foyer')
        return (AB + TA + TB + TC + TD + TE - TF + TG 
                   + TH + TO - TP + UZ + TZ + WA + WB 
                   + WC + WE)

    elif self.year == 2006:
        
        TC = table.getFoyer('vous', 'f8tc', 'foyer')
        TE = table.getFoyer('vous', 'f8te', 'foyer')
        TO = table.getFoyer('vous', 'f8to', 'foyer')
        TP = table.getFoyer('vous', 'f8tp', 'foyer')
        UZ = table.getFoyer('vous', 'f8uz', 'foyer')
        TZ = table.getFoyer('vous', 'f8tz', 'foyer')
        WA = table.getFoyer('vous', 'f8wa', 'foyer')
        WB = table.getFoyer('vous', 'f8wb', 'foyer')
        WC = table.getFoyer('vous', 'f8wc', 'foyer')
        WD = table.getFoyer('vous', 'f8wd', 'foyer')
        WE = table.getFoyer('vous', 'f8we', 'foyer')
        WR = table.getFoyer('vous', 'f8wr', 'foyer')
        WS = table.getFoyer('vous', 'f8ws', 'foyer')
        WT = table.getFoyer('vous', 'f8wt', 'foyer')
        WU = table.getFoyer('vous', 'f8wu', 'foyer')
        return (AB + TA + TB + TC + TE - TF + TG + TH 
                   + TO - TP + UZ + TZ + WA + WB + WC 
                   + WD + WE + WR + WS + WT + WU)


    elif self.year == 2007:

        TC = table.getFoyer('vous', 'f8tc', 'foyer')
        TE = table.getFoyer('vous', 'f8te', 'foyer')
        TO = table.getFoyer('vous', 'f8to', 'foyer')
        TP = table.getFoyer('vous', 'f8tp', 'foyer')
        UZ = table.getFoyer('vous', 'f8uz', 'foyer')
        TZ = table.getFoyer('vous', 'f8tz', 'foyer')
        WA = table.getFoyer('vous', 'f8wa', 'foyer')
        WB = table.getFoyer('vous', 'f8wb', 'foyer')
        WC = table.getFoyer('vous', 'f8wc', 'foyer')
        WD = table.getFoyer('vous', 'f8wd', 'foyer')
        WR = table.getFoyer('vous', 'f8wr', 'foyer')
        WS = table.getFoyer('vous', 'f8ws', 'foyer')
        WT = table.getFoyer('vous', 'f8wt', 'foyer')
        WU = table.getFoyer('vous', 'f8wu', 'foyer')
        WV = table.getFoyer('vous', 'f8wv', 'foyer')
        WX = table.getFoyer('vous', 'f8wx', 'foyer')
        return (AB + TA + TB + TC + TE - TF + TG + TH 
                   + TO - TP + UZ + TZ + WA + WB + WC 
                   + WD + WR + WS + WT + WU + WV + WX)
        
    elif self.year == 2008:
        TC = table.getFoyer('vous', 'f8tc', 'foyer')
        TE = table.getFoyer('vous', 'f8te', 'foyer')
        TO = table.getFoyer('vous', 'f8to', 'foyer')
        TP = table.getFoyer('vous', 'f8tp', 'foyer')
        UZ = table.getFoyer('vous', 'f8uz', 'foyer')
        TZ = table.getFoyer('vous', 'f8tz', 'foyer')
        WA = table.getFoyer('vous', 'f8wa', 'foyer')
        WB = table.getFoyer('vous', 'f8wb', 'foyer')
        WC = table.getFoyer('vous', 'f8wc', 'foyer')
        WD = table.getFoyer('vous', 'f8wd', 'foyer')
        WE = table.getFoyer('vous', 'f8we', 'foyer')
        WR = table.getFoyer('vous', 'f8wr', 'foyer')
        WS = table.getFoyer('vous', 'f8ws', 'foyer')
        WT = table.getFoyer('vous', 'f8wt', 'foyer')
        WU = table.getFoyer('vous', 'f8wu', 'foyer')
        WV = table.getFoyer('vous', 'f8wv', 'foyer')
        WX = table.getFoyer('vous', 'f8wx', 'foyer')
        return (AB + TA + TB + TC + TE - TF + TG + TH 
                   + TO - TP + UZ + TZ + WA + WB + WC 
                   + WD + WE + WR + WS + WT + WU + WV + WX)

    elif self.year == 2009:
        TO = table.getFoyer('vous', 'f8to', 'foyer')
        TP = table.getFoyer('vous', 'f8tp', 'foyer')
        UZ = table.getFoyer('vous', 'f8uz', 'foyer')
        TZ = table.getFoyer('vous', 'f8tz', 'foyer')
        WA = table.getFoyer('vous', 'f8wa', 'foyer')
        WB = table.getFoyer('vous', 'f8wb', 'foyer')
        WD = table.getFoyer('vous', 'f8wd', 'foyer')
        WE = table.getFoyer('vous', 'f8we', 'foyer')
        WR = table.getFoyer('vous', 'f8wr', 'foyer')
        WS = table.getFoyer('vous', 'f8ws', 'foyer')
        WT = table.getFoyer('vous', 'f8wt', 'foyer')
        WU = table.getFoyer('vous', 'f8wu', 'foyer')
        WV = table.getFoyer('vous', 'f8wv', 'foyer')
        WX = table.getFoyer('vous', 'f8wx', 'foyer')
        WY = table.getFoyer('vous', 'f8wy', 'foyer')
        return (AB + TA + TB - TF + TG + TH + TO - TP 
                   + UZ + TZ + WA + WB + WD + WE + WR 
                   + WS + WT + WU + WV + WX + WY)

    elif self.year == 2010:
        TC = table.getFoyer('vous', 'f8te', 'foyer')
        TE = table.getFoyer('vous', 'f8te', 'foyer')
        TO = table.getFoyer('vous', 'f8to', 'foyer')
        TP = table.getFoyer('vous', 'f8tp', 'foyer')
        UZ = table.getFoyer('vous', 'f8uz', 'foyer')
        TZ = table.getFoyer('vous', 'f8tz', 'foyer')
        WA = table.getFoyer('vous', 'f8wa', 'foyer')
        WB = table.getFoyer('vous', 'f8wb', 'foyer')
        WD = table.getFoyer('vous', 'f8wd', 'foyer')
        WE = table.getFoyer('vous', 'f8we', 'foyer')
        WR = table.getFoyer('vous', 'f8wr', 'foyer')
        WT = table.getFoyer('vous', 'f8wt', 'foyer')
        WU = table.getFoyer('vous', 'f8wu', 'foyer')
        WV = table.getFoyer('vous', 'f8wv', 'foyer')
        return (AB + TA + TB + TC + TE - TF
                   + TG + TO - TP + TH + UZ
                   + TZ + WA + WB + WD + WE
                   + WR + WT + WU + WV)

def divide(self, P, table):
    '''
    Crédit d'impôt dividendes
    '''
    
    DC = table.getFoyer('vous', 'f2dc', 'foyer')
    GR = table.getFoyer('vous', 'f2gr', 'foyer')
    max1 = P.divide.max*(self.marpac+1)
    return minimum(P.divide.taux*(DC + GR), max1)

def percvm(self, P, table):
    '''
    Crédit d’impôt pertes sur cessions de valeurs mobilières (3W)
    '''
    return zeros(self.taille)

def direpa(self, P, table):
    '''
    Crédit d’impôt directive « épargne » (case 2BG)
    '''
    return table.getFoyer('vous', 'f2bg', 'foyer')

def accult(self, P, table):
    '''
    Acquisition de biens culturels (case 7UO)
    '''
    return P.accult.taux*table.getFoyer('vous', 'f7uo', 'foyer')

def mecena(self, P, table):
    '''
    Mécénat d'entreprise (case 7US)
    '''
    return table.getFoyer('vous', 'f7us', 'foyer')

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
    WF = table.getFoyer('vous', 'f7wf', 'foyer')
    WH = table.getFoyer('vous', 'f7wh', 'foyer')
    WK = table.getFoyer('vous', 'f7wk', 'foyer')
    WQ = table.getFoyer('vous', 'f7wq', 'foyer')
    SB = table.getFoyer('vous', 'f7sb', 'foyer')
    SD = table.getFoyer('vous', 'f7sd', 'foyer')
    SE = table.getFoyer('vous', 'f7se', 'foyer')
    SH = table.getFoyer('vous', 'f7sh', 'foyer')
     
    n = self.nbF + self.nbJ + self.nbR + self.nbH/2
    if self.year == 2005:
        max0 = (P.quaenv.max*(1+self.marpac) + 
                P.quaenv.pac1*(n>=1) +
                P.quaenv.pac2*(n>=2) +
                P.quaenv.pac2*(maximum(n-2,0)) )
                
    elif self.year >= 2006:
        max0 = P.quaenv.max*(1+self.marpac) + P.quaenv.pac1*n
    
    if self.year == 2005:
        WG = table.getFoyer('vous', 'f7wg', 'foyer')    
        max1 = maximum(0, max0 - WF)
        max2 = maximum(0, max1 - WG)
        return (P.quaenv.taux_wf*minimum(WF, max0) +
                P.quaenv.taux_wg*minimum(WG, max1) +
                P.quaenv.taux_wh*minimum(WH, max2) )

    elif self.year in (2006, 2007, 2008):
        WG = table.getFoyer('vous', 'f7wg', 'foyer')    
        max1 = maximum(0, max0 - WF)
        max2 = maximum(0, max1 - WG)
        max3 = maximum(0, max2 - WH)
        return (P.quaenv.taux_wf*minimum(WF, max0) +
                P.quaenv.taux_wg*minimum(WG, max1) +
                P.quaenv.taux_wh*minimum(WH, max2) +
                P.quaenv.taux_wq*minimum(WQ, max3) )

    elif self.year == 2009:
        WG = table.getFoyer('vous', 'f7wg', 'foyer')
        SC = table.getFoyer('vous', 'f7sc', 'foyer')
        max1 = maximum(0, max0 - WF)
        max2 = maximum(0, max1 - SE)
        max3 = maximum(0, max2 - WK)
        max4 = maximum(0, max3 - SD)
        max5 = maximum(0, max4 - WG)
        max6 = maximum(0, max5 - SC)
        max7 = maximum(0, max6 - WH)
        return (P.quaenv.taux_wf*minimum(WF, max0) +
                P.quaenv.taux_se*minimum(SE, max1) +
                P.quaenv.taux_wk*minimum(WK, max2) +
                P.quaenv.taux_sd*minimum(SD, max3) +
                P.quaenv.taux_wg*minimum(WG, max4) +
                P.quaenv.taux_sc*minimum(SC, max5) +
                P.quaenv.taux_wh*minimum(WH, max6) +
                P.quaenv.taux_sb*minimum(SB, max7) )

    elif self.year == 2010:
        max1 = maximum(0, max0 - WF)
        max2 = maximum(0, max1 - SE)
        max3 = maximum(0, max2 - WK)
        max4 = maximum(0, max3 - SD)
        max5 = maximum(0, max4 - WH)
        max6 = maximum(0, max5 - SB)
        max7 = maximum(0, max6 - WQ)
        return (P.quaenv.taux_wf*minimum(WF, max0) +
                P.quaenv.taux_se*minimum(SE, max1) +
                P.quaenv.taux_wk*minimum(WK, max2) +
                P.quaenv.taux_sd*minimum(SD, max3) +
                P.quaenv.taux_wh*minimum(WH, max4)+
                P.quaenv.taux_sb*minimum(SB, max5) +
                P.quaenv.taux_wq*minimum(WQ, max6) +
                P.quaenv.taux_sh*minimum(SH, max7) )

def aidper(self, P, table):
    '''
    Crédits d’impôt pour dépenses en faveur de l’aide aux personnes 
    (cases 7WI, 7WJ, 7WL et 7SF).
    '''
    WI = table.getFoyer('vous', 'f7wf', 'foyer')
    WJ = table.getFoyer('vous', 'f7wj', 'foyer')
    WL = table.getFoyer('vous', 'f7wl', 'foyer')
    SF = table.getFoyer('vous', 'f7sf', 'foyer')
    
    n = self.nbF + self.nbJ + self.nbR + self.nbH/2
    if self.year <= 2005:
        max0 = (P.aidper.max*(1+self.marpac) + 
                P.aidper.pac1*(n>=1) +
                P.aidper.pac2*(n>=2) +
                P.aidper.pac2*(maximum(n-2,0)) )
               
    elif self.year >= 2006:
        max0 = P.aidper.max*(1+self.marpac) + P.aidper.pac1*n

    if self.year in (2002,2003):
        return P.aidper.taux_wi*minimum(WI, max0) # TODO enfant en résidence altérnée
    elif self.year <= 2009:
        max1 = maximum(0, max0 - WJ)
        return (P.aidper.taux_wj*minimum(WJ, max0) +
                P.aidper.taux_wi*minimum(WI, max1) )
    elif self.year == 2010:
        max1 = maximum(0, max0 - WL)
        max2 = maximum(0, max1 - SF)
        max3 = maximum(0, max2 - WJ)
        return (P.aidper.taux_wl*minimum(WL, max0) +
                P.aidper.taux_sf*minimum(SF, max1) +
                P.aidper.taux_wj*minimum(WJ, max2) +
                P.aidper.taux_wi*minimum(WI, max3) )

def acqgpl(self, P, table):
    # crédit d'impôt pour dépense d'acquisition ou de transformation d'un véhicule GPL ou mixte
    if 2002 <= self.year <= 2007:
        UP = table.getFoyer('vous', 'f7up', 'foyer')
        UQ = table.getFoyer('vous', 'f7uq', 'foyer')
        return UP*P.acqgpl.mont_up + UQ*P.acqgpl.mont_uq

def drbail(self, P, table):
    '''
    Crédit d’impôt représentatif de la taxe additionnelle au droit de bail (case 4TQ)
    '''
    return P.drbail.taux*table.getFoyer('vous', 'f4tq', 'foyer')

def garext(self, P, table):
    '''
    Frais de garde des enfants à l’extérieur du domicile (cases 7GA à 7GC et 7GE à 7GG)
    '''
    max1 = P.garext.max
    GA = table.getFoyer('vous', 'f4ga', 'foyer')
    GB = table.getFoyer('vous', 'f4gb', 'foyer')
    GC = table.getFoyer('vous', 'f4gc', 'foyer')
    GE = table.getFoyer('vous', 'f4ge', 'foyer')
    GF = table.getFoyer('vous', 'f4gf', 'foyer')
    GG = table.getFoyer('vous', 'f4gg', 'foyer')
    
    return P.garext.taux*(minimum(GA, max1) + 
                          minimum(GB, max1) +
                          minimum(GC, max1) +
                          minimum(GE, max1/2) +
                          minimum(GF, max1/2) +
                          minimum(GG, max1/2))
def preetu(self, P, table):
    '''
    Crédit d’impôt pour souscription de prêts étudiants (cases 7UK, 7VO et 7TD)
    '''
    UK = table.getFoyer('vous', 'f7uk', 'foyer')
    VO = table.getFoyer('vous', 'f7vo', 'foyer')
    TD = table.getFoyer('vous', 'f7td', 'foyer')
    
    if self.year == 2005: 
        max1 = P.preetu.max
    elif self.year >= 2006:
        max1 = P.preetu.max*(1+VO)
    if self.year in (2005,2006,2007):
        return P.preetu.taux*minimum(UK, max1)
    elif self.year >=2008:
        return P.preetu.taux*minimum(UK, P.preetu.max) + P.preetu.taux*minimum(TD, max1)

def saldom(self, P, table):
    '''
    Crédit d’impôt emploi d’un salarié à domicile (cases 7DB, 7DG)
    '''
    # TODO, TODO, TODO check avant 2010
    
    DG = table.getFoyer('vous', 'f7dg', 'foyer')
    isinvalid = DG
    DL = table.getFoyer('vous', 'f7dl', 'foyer')
    DB = table.getFoyer('vous', 'f7db', 'foyer')  # dépense pour crédit d'impôt
    
    if self.year in (2007,2008):
        nbpacmin = self.nbF + self.nbH/2 + self.nbJ + self.nbN + DL
        maxBase = P.saldom.max1
        maxDuMaxNonInv = P.saldom.max2
        maxNonInv = minimum(maxBase + P.saldom.pac*nbpacmin, maxDuMaxNonInv)
        maxEffectif = maxNonInv*lnot(isinvalid) + P.saldom.max3*isinvalid
        
    elif self.year in (2009, 2010):
        DQ = table.getFoyer('vous', 'f7dq', 'foyer')  # 1èere année
        annee1 = DQ
        nbpacmin = self.nbF + self.nbH/2 + self.nbJ + self.nbN + DL
        maxBase = P.saldom.max1*lnot(annee1) + P.saldom.max1_1ereAnnee*annee1
        maxDuMaxNonInv = P.saldom.max2*lnot(annee1) + P.saldom.max2_1ereAnnee*annee1
        maxNonInv = minimum(maxBase + P.saldom.pac*nbpacmin, maxDuMaxNonInv)
        maxEffectif = maxNonInv*lnot(isinvalid) + P.saldom.max3*isinvalid
        
        
        
    '''
   
    DL = table.getFoyer('vous', 'f7dl', 'foyer')
    DQ = table.getFoyer('vous', 'f7dq', 'foyer')
    DB = table.getFoyer('vous', 'f7db', 'foyer')
    DG = table.getFoyer('vous', 'f7dg', 'foyer')

    
    isinvalid = DG
            
    annee1 = DQ
    nbpacmin = self.nbF + self.nbH / 2 + self.nbJ + self.nbN + DL
    maxBase = P.saldom.max1 * lnot(annee1) + P.saldom.max1_1ereAnnee * annee1
    maxDuMaxNonInv = P.saldom.max2 * lnot(annee1) + P.saldom.max2_1ereAnnee * annee1
    maxDuMax = maxDuMaxNonInv * lnot(isinvalid) + P.saldom.max3 * isinvalid
    maxEffectif = minimum(maxBase + P.saldom.pac * nbpacmin, maxDuMax)
    maxEffectif = maximum(maxEffectif,P.saldom.max3*isinvalid)
    '''
    
    '''
    elif self.year in (2007,2008):
        DL = table.getFoyer('vous', 'f7dl', 'foyer')
        DB = table.getFoyer('vous', 'f7db', 'foyer')  # Crédit d'impôt
        nbpacmin = self.nbF + self.nbH/2 + self.nbJ + self.nbN + DL
        maxBase = P.saldom.max1
        maxDuMaxNonInv = P.saldom.max2
        maxNonInv = minimum(maxBase + P.saldom.pac*nbpacmin, maxDuMaxNonInv)
        maxEffectif = maxNonInv*lnot(isinvalid) + P.saldom.max3*isinvalid
        max1 = maxEffectif - minimum(DB, maxEffectif)
            
    elif self.year in (2009, 2010):
        DL = table.getFoyer('vous', 'f7dl', 'foyer')  # 
        DQ = table.getFoyer('vous', 'f7dq', 'foyer')  # 1èere année
        DB = table.getFoyer('vous', 'f7db', 'foyer')  # Crédit d'impôt
        
        annee1 = DQ
        nbpacmin = self.nbF + self.nbH/2 + self.nbJ + self.nbN + DL
        maxBase = P.saldom.max1*lnot(annee1) + P.saldom.max1_1ereAnnee*annee1
        maxDuMaxNonInv = P.saldom.max2*lnot(annee1) + P.saldom.max2_1ereAnnee*annee1
        maxNonInv = minimum(maxBase + P.saldom.pac*nbpacmin, maxDuMaxNonInv)
        maxEffectif = maxNonInv*lnot(isinvalid) + P.saldom.max3*isinvalid
        max1 = maxEffectif - minimum(DB, maxEffectif)

    
    '''
    
    return P.saldom.taux*minimum(DB, maxEffectif)


def inthab(self, P, table):
    '''
    Crédit d’impôt intérêts des emprunts pour l’habitation principale (cases 7VW, 7VX, 7VY et 7VZ)
    '''
    VW = table.getFoyer('vous', 'f7vw', 'foyer')
    VX = table.getFoyer('vous', 'f7vx', 'foyer')
    VY = table.getFoyer('vous', 'f7vy', 'foyer')
    VZ = table.getFoyer('vous', 'f7vz', 'foyer')
    
    invalide = self.caseP |self.caseF | (self.nbG!=0) | (self.nbR!=0)
    nb = self.nbF + self.nbH/2 + self.nbR + self.nbJ + self.nbN
    max0 = P.inthab.max*(self.marpac+1)*(1+invalide) + nb*P.inthab.add

    if self.year == 2007:
        return zeros(self.taille)
    if self.year == 2008:  
        max1 = minimum(max0 - VY, 0)
        return (P.inthab.taux1*minimum(VY, max0) + 
                P.inthab.taux3*minimum(VZ, max1) )
    if self.year == 2009:
        max1 = minimum(max0 - VX, 0)
        max2 = minimum(max1 - VY, 0)
        return (P.inthab.taux1*minimum(VX, max0) + 
                P.inthab.taux1*minimum(VY, max1) + 
                P.inthab.taux3*minimum(VZ, max2) )
    if self.year == 2010:
        max1 = minimum(max0 - VX, 0)
        max2 = minimum(max1 - VY, 0)
        max3 = minimum(max2 - VW, 0)
        return (P.inthab.taux1*minimum(VX, max0) + 
                P.inthab.taux1*minimum(VY, max1) + 
                P.inthab.taux2*minimum(VW, max2) + 
                P.inthab.taux3*minimum(VZ, max3) )

def assloy(self, P, table):
    '''
    Crédit d’impôt primes d’assurance pour loyers impayés (case 4BF)
    '''
    return P.assloy.taux*table.getFoyer('vous', 'f4bf', 'foyer')

def autent(self, P, table):
    '''
    Auto-entrepreneur : versements d’impôt sur le revenu (case 8UY)
    '''
    return zeros(self.taille)

def aidmob(self, P, table):
    # crédit d'impôt aide à la mobilité
    AR = table.getFoyer('vous', 'f1ar', 'foyer')
    BR = table.getFoyer('vous', 'f1br', 'foyer')
    CR = table.getFoyer('vous', 'f1cr', 'foyer')
    DR = table.getFoyer('vous', 'f1dr', 'foyer')
    ER = table.getFoyer('vous', 'f1er', 'foyer')
    return (AR + BR + CR + DR + ER)*P.aidmob.montant

def jeunes(self, P, table):
    # crédit d'impôt en faveur des jeunes
    return  zeros(self.taille) # D'après  le document num. 2041 GY
                                # somme calculée sur formulaire 2041;
