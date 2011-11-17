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
from numpy import minimum as min_, maximum as max_, zeros, logical_not as not_

def niches(year):
    '''
    Renvoie la liste des réductions d'impôt à intégrer en fonction de l'année
    '''
    if   year == 2002:
        niches = [donapd, dfppce, saldom, cotsyn, prcomp, spfcpi, cappme, intemp, 
                  invfor, garext, daepad, rsceha, assvie, invrev, domlog, adhcga, 
                  ecpess, doment]
    elif year == 2003:
        niches = [donapd, dfppce, saldom, cotsyn, prcomp, spfcpi, cappme, intemp, 
                  repsoc, invfor, garext, daepad, rsceha, assvie, invrev, domlog, 
                  adhcga, ecpess, doment]
    elif year == 2004:
        niches = [donapd, dfppce, saldom, cotsyn, prcomp, spfcpi, cappme, intcon, 
                  repsoc, invfor, garext, daepad, rsceha, assvie, invlst, domlog, 
                  adhcga, ecpess, doment]
    elif year == 2005:
        niches = [donapd, dfppce, cotsyn, saldom, intagr, prcomp, spfcpi, cappme, 
                  intcon, repsoc, invfor, daepad, rsceha, invlst, domlog, adhcga, 
                  ecpess, doment]
    elif year == 2006:
        niches = [donapd, dfppce, cotsyn, saldom, intagr, prcomp, spfcpi, sofica, 
                  cappme, repsoc, invfor, deffor, daepad, rsceha, invlst, domlog, 
                  adhcga, ecpess, doment]
    elif year == 2007:
        niches = [donapd, dfppce, cotsyn, saldom, intagr, prcomp, spfcpi, sofica, 
                  cappme, repsoc, invfor, deffor, daepad, rsceha, invlst, domlog, 
                  adhcga, creaen, ecpess, doment]
    elif year == 2008:
        niches = [donapd, dfppce, cotsyn, saldom, intagr, prcomp, spfcpi, mohist, 
                  sofica, cappme, repsoc, invfor, deffor, daepad, rsceha, invlst, 
                  domlog, adhcga, creaen, ecpess, doment]
    elif year == 2009:
        niches = [donapd, dfppce, cotsyn, resimm, sofipe, ecodev, saldom, intagr, 
                  prcomp, spfcpi, mohist, sofica, cappme, repsoc, invfor, deffor, 
                  daepad, rsceha, invlst, domlog, adhcga, creaen, ecpess, scelli, 
                  locmeu, doment]
    elif year == 2010:
        niches = [donapd, dfppce, cotsyn, resimm, patnat, sofipe, saldom, intagr, 
                  prcomp, spfcpi, mohist, sofica, cappme, repsoc, invfor, deffor, 
                  daepad, rsceha, invlst, domlog, adhcga, creaen, ecpess, scelli, 
                  locmeu, doment, domsoc]

    return niches


def donapd(self, P, table):
    '''
    Dons effectués à  des organises d'aide aux personnes en difficulté
    2002-
    '''
    UD = table.get('vous', 'f7ud', 'foy', 'foyer')
    return P.donapd.taux*min_(UD, P.donapd.max)

def dfppce(self, P, table):   
    '''
    Dons aux autres oeuvres et dons effectués pour le financement des partis
    politiques et des compagnes électorales
    2002-
    '''
    base = table.get('vous', 'f7uf', 'foy', 'foyer')
    if self.year >= 2004: base += table.get('vous', 'f7xs', 'foy', 'foyer')
    if self.year >= 2005: base += table.get('vous', 'f7xt', 'foy', 'foyer')
    if self.year >= 2006: base += table.get('vous', 'f7xu', 'foy', 'foyer')
    if self.year >= 2007: base += table.get('vous', 'f7xw', 'foy', 'foyer')
    if self.year >= 2008: base += table.get('vous', 'f7xy', 'foy', 'foyer')
    max1 = P.dfppce.max*self.rbg_int
    return P.dfppce.taux*min_(base, max1)
    # TODO: note de bas de page

def cotsyn(self, P, table):
    '''
    Cotisations syndicales
    2002-
    '''
    tx = P.cotsyn.seuil
    
    salv, salc, salp = table.get(['vous', 'conj',  'pac1'], 'sal', 'foy')
    chov, choc, chop = table.get(['vous', 'conj',  'pac1'], 'cho', 'foy')
    rstv, rstc, rstp = table.get(['vous', 'conj',  'pac1'], 'rst', 'foy')
    maxv = (salv+chov+rstv)*tx
    maxc = (salc+choc+rstc)*tx
    maxp = (salp+chop+rstp)*tx
    
    AC = table.get('vous', 'f7ac', 'foy', 'foyer')
    AE = table.get('vous', 'f7ae', 'foy', 'foyer') 
    AG = table.get('vous', 'f7ag', 'foy', 'foyer')
    return P.cotsyn.taux*(min_(AC,maxv)  + min_(AE,maxc) + min_(AG,maxp))

def resimm(self, P, table):
    '''
    Travaux de restauration immobilière (cases 7RA et 7RB)
    2009-
    '''
    RA = table.get('vous', 'f7ra', 'foy', 'foyer')
    RB = table.get('vous', 'f7rb', 'foy', 'foyer')
    max1 = P.resimm.max
    max2 = max_(max1 - RB, 0)
    return P.resimm.taux_rb*min_(RB, max1)+ P.resimm.taux_ra*min_(RA, max2)

def patnat(self, P, table):
    '''
    Dépenses de protections du patrimoine naturel (case 7KA)
    2010-
    '''
    KA = table.get('vous', 'f7ka', 'foy', 'foyer')
    max1 = P.patnat.max
    return P.patnat.taux*min_(KA, max1)

def sofipe(self, P, table):
    '''
    Souscription au capital d’une SOFIPECHE (case 7GS)
    2009-
    '''
    GS = table.get('vous', 'f7gs', 'foy', 'foyer')
    max1 = min_(P.sofipe.max*(self.marpac+1), P.sofipe.base*self.rbg_int) # page3 ligne 18
    return P.sofipe.taux*min_(GS, max1)

def ecodev(self, P, table):
    '''
    Sommes versées sur un compte épargne codéveloppement (case 7UH)
    2009
    '''
    UH = table.get('vous', 'f7uh', 'foy', 'foyer')
    return min_(UH, min_(P.ecodev.base*self.rbg_int, P.ecodev.max)) # page3 ligne 18

def saldom(self, P, table):
    '''
    Sommes versées pour l'emploi d'un salariés à  domicile
    2002-
    En 2006 : Le plafond des dépenses ouvrant droit à réduction d’impôt est de
    12 000 € majoré de 1 500 € par enfant mineur compté à charge (750 €
    si l’enfant est en résidence alternée), par enfant rattaché (que le rattachement
    prenne la forme d’une majoration du quotient familial ou d’un
    abattement), par membre du foyer fiscal âgé de plus de 65 ans ou par
    ascendant âgé de plus de 65 ans bénéficiant de l’APA lorsque vous supportez
    personnellement les frais au titre de l’emploi d’un salarié travaillant
    chez l’ascendant. Ce plafond ne peut excéder 15 000 €. Le plafond
    est de 20 000 € si un membre de votre foyer fiscal est titulaire de
    la carte d’invalidité d’au moins 80 % ou d’une pension d’invalidité de 3e
    catégorie ou si vous percevez un complément d’allocation d’éducation
    spéciale pour l’un de vos enfants à charge.
    '''
    DF = table.get('vous', 'f7df', 'foy', 'foyer')
    DG = table.get('vous', 'f7dg', 'foy', 'foyer')
    isinvalid = DG
    
    if self.year in (2002, 2003, 2004):
        max1 = P.saldom.max1*not_(isinvalid) + P.saldom.max3*isinvalid
    elif self.year in (2005,2006):
        DL = table.get('vous', 'f7dl', 'foy', 'foyer')
        nbpacmin = self.nbF + self.nbH/2 + self.nbJ + self.nbN + DL
        maxBase = P.saldom.max1
        maxDuMaxNonInv = P.saldom.max2
        maxNonInv = min_(maxBase + P.saldom.pac*nbpacmin, maxDuMaxNonInv)
        max1 = maxNonInv*not_(isinvalid) + P.saldom.max3*isinvalid
                 
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
                
    return P.saldom.taux*min_(DF, max1)

def intagr(self, P, table):
    '''
    Intérêts pour paiement différé accordé aux agriculteurs
    2005-
    '''
    UM = table.get('vous', 'f7um', 'foy', 'foyer')
    max1 = P.intagr.max*(1+self.marpac)
    return P.intagr.taux*min_(UM, max1)

def prcomp(self, P, table):
    '''
    Prestations compensatoires
    2002-2010
    '''
    WM = table.get('vous', 'f7wm', 'foy', 'foyer')
    WN = table.get('vous', 'f7wn', 'foy', 'foyer')
    WO = table.get('vous', 'f7wo', 'foy', 'foyer')
    WP = table.get('vous', 'f7wp', 'foy', 'foyer')
    
    div = (WO==0)*1 + WO # Pour éviter les divisions par zéro
    
    return ((WM == 0)*((WN==WO)*P.prcomp.taux*min_(WN,P.prcomp.seuil) +
                              (WN<WO)*(WO<=P.prcomp.seuil)*P.prcomp.taux*WN +
                              max_(0,(WN<WO)*(WO> P.prcomp.seuil)*P.prcomp.taux*P.prcomp.seuil*WN/div) +
                              P.prcomp.taux*WP ) +
            (WM != 0)*((WN==WM)*(WO<=P.prcomp.seuil)*P.prcomp.taux*WM + 
                              max_(0,(WN==WM)*(WO>=P.prcomp.seuil)*P.prcomp.taux*WM/div) + 
                              (WN>WM)*(WO<=P.prcomp.seuil)*P.prcomp.taux*WN  + 
                              max_(0,(WN>WM)*(WO>=P.prcomp.seuil)*P.prcomp.taux*WN/div)) +
             P.prcomp.taux*WP)

def spfcpi(self, P, table):
    '''
    Souscription de parts de fonds communs de placement dans l'innovation, 
    de fonds d'investissement de proximité
    2002-
    '''
    max1 = P.spfcpi.max*(self.marpac+1)
    GQ = table.get('vous', 'f7gq', 'foy', 'foyer')

    if self.year <= 2002:
        return P.spfcpi.taux1*min_(GQ, max1)
    elif self.year <= 2006:
        FQ = table.get('vous', 'f7fq', 'foy', 'foyer')
        return (P.spfcpi.taux1*min_(GQ, max1) + 
                P.spfcpi.taux1*min_(FQ, max1) )
    elif self.year <= 2010:
        FQ = table.get('vous', 'f7fq', 'foy', 'foyer')
        FM = table.get('vous', 'f7fm', 'foy', 'foyer')
        return (P.spfcpi.taux1*min_(GQ, max1) + 
                P.spfcpi.taux1*min_(FQ, max1) +
                P.spfcpi.taux2*min_(FM, max1) )

def mohist(self, P, table):
    '''
    Travaux de conservation et de restauration d’objets classés monuments historiques (case NZ)
    2008-
    '''
    NZ = table.get('vous', 'f7nz', 'foy', 'foyer')
    return P.mohist.taux*min_(NZ, P.mohist.max)

def sofica(self, P, table):
    '''
    Souscriptions au capital de SOFICA
    2006-
    '''
    GN = table.get('vous', 'f7gn', 'foy', 'foyer')
    FN = table.get('vous', 'f7fn', 'foy', 'foyer')
    max0 = min_(P.sofica.taux1*max_(self.rng,0), P.sofica.max)
    max1 = min_(0, max0 - GN)
    return P.sofica.taux2*min_(GN, max0) + \
           P.sofica.taux3*min_(FN, max1)

def cappme(self, P, table):
    '''
    Souscriptions au capital des PME
    2002-
    '''
    base = table.get('vous', 'f7cf', 'foy', 'foyer')
    if self.year >= 2003: base += table.get('vous', 'f7cl', 'foy', 'foyer')
    if self.year >= 2004: base += table.get('vous', 'f7cm', 'foy', 'foyer')
    if self.year >= 2005: base += table.get('vous', 'f7cn', 'foy', 'foyer')
    seuil = P.cappme.seuil*(self.marpac + 1)

    if self.year <= 2008:
        return P.cappme.taux*min_(base,seuil)
    elif self.year <= 2010:
        CU = table.get('vous', 'f7cu', 'foy', 'foyer')
        seuil_tpe = P.cappme.seuil_tpe*(self.marpac + 1)
        return P.cappme.taux*(min_(base,seuil)+min_(CU, seuil_tpe))

def intemp(self, P, table):
    '''
    Intérêts d'emprunts
    2002-2003
    '''
    WG = table.get('vous', 'f7wg', 'foy', 'foyer')
    max1 = P.intemp.max + P.intemp.pac*self.nbPAC
    return P.intemp.taux*min_(WG, max1)

def intcon(self, P, table):
    '''
    Intérêts des prêts à la consommation (case UH)
    2004-2005
    '''
    max1 = P.intcon.max
    UH = table.get('vous', 'f7uh', 'foy', 'foyer')
    return P.intcon.taux*min_(UH, max1)

def repsoc(self, P, table):
    '''
    Intérèts d'emprunts pour reprises de société
    '''
    FH = table.get('vous', 'f7fh', 'foy', 'foyer')
    seuil = P.repsoc.seuil*(self.marpac+1)
    return P.repsoc.taux*min_(FH, seuil)
    
def invfor(self, P, table):
    '''
    Investissements forestiers
    '''
    UN = table.get('vous', 'f7un', 'foy', 'foyer')
    if self.year <= 2002:
        seuil = P.invfor.seuil*(self.marpac + 1)
        return P.invfor.taux*min_(UN, seuil)
    elif self.year <= 2008:
        return P.invfor.taux*UN
    else:
        seuil = 0 # vérifier la notice à partir de 2009
        return P.invfor.taux*min_(UN, seuil) 

def garext(self, P, table):
    '''
    Frais de garde des enfants à l’extérieur du domicile (cases GA, GB, GC de la 2042)
    et GE, GF, GG
    2002-2005
    '''
    max1 = P.garext.max 
    GA = table.get('vous', 'f7ga', 'foy', 'foyer')
    GB = table.get('vous', 'f7gb', 'foy', 'foyer')
    GC = table.get('vous', 'f7gc', 'foy', 'foyer')
    if self.year <= 2002:
        return P.garext.taux*(min_(GA, max1) + 
                              min_(GB, max1) + 
                              min_(GC, max1) )
    elif self.year <= 2005:
        GE = table.get('vous', 'f7ge', 'foy', 'foyer')
        GF = table.get('vous', 'f7gf', 'foy', 'foyer')
        GG = table.get('vous', 'f7gg', 'foy', 'foyer')
        return P.garext.taux*(min_(GA, max1) + 
                              min_(GB, max1) + 
                              min_(GC, max1) + 
                              min_(GE, max1/2) + 
                              min_(GF, max1/2) + 
                              min_(GG, max1/2) )

def deffor(self, P, table):
    '''
    Défense des forêts contre l'incendie
    '''
    UC = table.get('vous', 'f7uc', 'foy', 'foyer')
    return P.deffor.taux*min_(UC, P.deffor.max )
    
def daepad(self, P, table):
    '''
    Dépenses d'accueil dans un établissement pour personnes âgées dépendantes
    '''
    CD = table.get('vous', 'f7cd', 'foy', 'foyer')
    CE = table.get('vous', 'f7ce', 'foy', 'foyer')
    return P.daepad.taux*(min_(CD, P.daepad.max) + min_(CE, P.daepad.max))

def rsceha(self, P, table):
    '''
    Rentes de survie et contrats d'épargne handicap
    '''
    GZ = table.get('vous', 'f7gz', 'foy', 'foyer')
    max1 = P.rsceha.seuil1 + (self.nbPAC - self.nbR + self.nbH/2)*P.rsceha.seuil2
    # TODO: verifier la formule précédente
    return P.rsceha.taux*min_(GZ, max1)

def assvie(self, P, table):
    '''
    Assurance-vie (cases GW, GX et GY de la 2042)
    2002-2004
    '''
    GW = table.get('vous', 'f7gw', 'foy', 'foyer')
    GX = table.get('vous', 'f7gx', 'foy', 'foyer')
    GY = table.get('vous', 'f7gy', 'foy', 'foyer')
    max1 = P.assvie.max + self.nbPAC*P.assvie.pac
    return P.assvie.taux*min_(GW + GX + GY, max1)

def invrev(self, P, table):
    '''
    Investissements locatifs dans les résidences de tourisme situées dans une zone de 
    revitalisation rurale (cases GS, GT, XG, GU et GV)
    '''
    return zeros(self.taille)

def invlst(self, P, table):
    '''
    Investissements locatifs dans le secteur de touristique
    '''
    seuil1 = P.invlst.seuil1*(1+self.marpac)
    seuil2 = P.invlst.seuil2*(1+self.marpac)
    seuil3 = P.invlst.seuil3*(1+self.marpac)
    XC = table.get('vous', 'f7xc', 'foy', 'foyer')
    if self.year == 2004: xc = P.invlst.taux_xc*min_(XC,seuil1/4)
    else: xc = P.invlst.taux_xc*min_(XC,seuil1/6)
    xd = P.invlst.taux_xd*table.get('vous', 'f7xd', 'foy', 'foyer')
    xe = P.invlst.taux_xe*min_(table.get('vous', 'f7xe', 'foy', 'foyer'),seuil1/6)
    xf = P.invlst.taux_xf*table.get('vous', 'f7xf', 'foy', 'foyer')
    xg = P.invlst.taux_xg*min_(table.get('vous', 'f7xg', 'foy', 'foyer'),seuil2)
    xh = P.invlst.taux_xh*min_(table.get('vous', 'f7xh', 'foy', 'foyer'), seuil3)
    xi = P.invlst.taux_xi*min_(table.get('vous', 'f7xi', 'foy', 'foyer'), seuil1/4)
    xj = P.invlst.taux_xj*table.get('vous', 'f7xj', 'foy', 'foyer')
    xk = P.invlst.taux_xk*table.get('vous', 'f7xk', 'foy', 'foyer')
    xl = P.invlst.taux_xl*min_(table.get('vous', 'f7xl', 'foy', 'foyer'), seuil1/6)
    xm = P.invlst.taux_xm*table.get('vous', 'f7xm', 'foy', 'foyer')
    xn = P.invlst.taux_xn*min_(table.get('vous', 'f7xn', 'foy', 'foyer'),seuil1/6)
    xo = P.invlst.taux_xo*table.get('vous', 'f7xo', 'foy', 'foyer')
    return xc + xd + xe + xf + xg + xh + xi + xj + xk + xl + xm + xn + xo
    
def domlog(self, P, table):
    '''
    Investissements OUTRE-MER dans le secteur du logement et autres secteurs d’activité
    2002-2009
    TODO: Plafonnement sur la notice
    '''
    if self.year <= 2002:
        UA = table.get('vous', 'f7ua', 'foy', 'foyer')
        UB = table.get('vous', 'f7ub', 'foy', 'foyer')
        UC = table.get('vous', 'f7uc', 'foy', 'foyer')
        UJ = table.get('vous', 'f7uj', 'foy', 'foyer')    
        return P.domlog.taux1*UJ + P.domlog.taux2*(UA + UB + UC) 
    if self.year <= 2004:
        UA = table.get('vous', 'f7ua', 'foy', 'foyer')
        UB = table.get('vous', 'f7ub', 'foy', 'foyer')
        UC = table.get('vous', 'f7uc', 'foy', 'foyer')
        UI = table.get('vous', 'f7ui', 'foy', 'foyer')
        UJ = table.get('vous', 'f7uj', 'foy', 'foyer')
        return P.domlog.taux1*UJ + P.domlog.taux2*(UA + UB + UC) + UI
    elif self.year <= 2007:
        UA = table.get('vous', 'f7ua', 'foy', 'foyer')
        UB = table.get('vous', 'f7ub', 'foy', 'foyer')
        UI = table.get('vous', 'f7ui', 'foy', 'foyer')
        UJ = table.get('vous', 'f7uj', 'foy', 'foyer')
        return P.domlog.taux1*UJ + P.domlog.taux2*(UA + UB ) + UI
    elif self.year <= 2008:
        UI = table.get('vous', 'f7ui', 'foy', 'foyer')    
        return UI
    elif self.year <= 2009:
        QB = table.get('vous', 'f7qb', 'foy', 'foyer')
        QC = table.get('vous', 'f7qc', 'foy', 'foyer')
        QD = table.get('vous', 'f7qd', 'foy', 'foyer')
        return QB + QC + QD
    elif self.year <= 2010:
        QB = table.get('vous', 'f7qb', 'foy', 'foyer')
        QC = table.get('vous', 'f7qc', 'foy', 'foyer')
        QL = table.get('vous', 'f7ql', 'foy', 'foyer')
        QT = table.get('vous', 'f7qt', 'foy', 'foyer')
        QM = table.get('vous', 'f7qm', 'foy', 'foyer')
        QD = table.get('vous', 'f7qd', 'foy', 'foyer')
        return QB + QC + QL + QT + QM + QD
 
def adhcga(self, P, table):
    '''
    Frais de comptabilité et d'adhésion à un CGA ou AA
    2002-
    '''
    FF = table.get('vous', 'f7ff', 'foy', 'foyer')
    FG = table.get('vous', 'f7fg', 'foy', 'foyer')
    return min_(FF, P.adhcga.max*FG)

def creaen(self, P, table):
    '''
    Aide aux créateurs et repreneurs d'entreprises
    TODO...
    '''
    if self.year <= 2008:
        FY = table.get('vous', 'f7fy', 'foy', 'foyer')
        GY = table.get('vous', 'f7gy', 'foy', 'foyer')
        return (P.creaen.base*FY + P.creaen.hand*GY )
    elif self.year == 2009:
        JY = table.get('vous', 'f7jy', 'foy', 'foyer')
        FY = table.get('vous', 'f7fy', 'foy', 'foyer')
        HY = table.get('vous', 'f7hy', 'foy', 'foyer')
        KY = table.get('vous', 'f7ky', 'foy', 'foyer')
        GY = table.get('vous', 'f7gy', 'foy', 'foyer')
        IY = table.get('vous', 'f7iy', 'foy', 'foyer')
        return (P.creaen.base*((JY + FY) + HY/2) +
                P.creaen.hand*((KY + GY) + IY/2) )
    elif self.year == 2010:
        JY = table.get('vous', 'f7jy', 'foy', 'foyer')
        FY = table.get('vous', 'f7fy', 'foy', 'foyer')
        HY = table.get('vous', 'f7hy', 'foy', 'foyer')
        LY = table.get('vous', 'f7ly', 'foy', 'foyer')
        KY = table.get('vous', 'f7ky', 'foy', 'foyer')
        GY = table.get('vous', 'f7gy', 'foy', 'foyer')
        IY = table.get('vous', 'f7iy', 'foy', 'foyer')
        MY = table.get('vous', 'f7my', 'foy', 'foyer')
        return (P.creaen.base*((JY + FY) + (HY + LY)/2) +
                P.creaen.hand*((KY + GY) + (IY + MY)/2) )
      
def ecpess(self, P, table):
    '''
    Enfants à charge poursuivant leurs études secondaires ou supérieures
    '''
    EA = table.get('vous', 'f7ea', 'foy', 'foyer')
    EB = table.get('vous', 'f7eb', 'foy', 'foyer')
    EC = table.get('vous', 'f7ec', 'foy', 'foyer')
    ED = table.get('vous', 'f7ed', 'foy', 'foyer')
    EF = table.get('vous', 'f7ef', 'foy', 'foyer')
    EG = table.get('vous', 'f7eg', 'foy', 'foyer')
    return (P.ecpess.col*(EA + EB/2) +
            P.ecpess.lyc*(EC + ED/2) +
            P.ecpess.sup*(EF + EG/2) )

def scelli(self, P, table):
    '''
    Investissements locatif neufs : Dispositif SCELLIER (cases 7HJ et 7HK)
    '''
    return zeros(self.taille)

def locmeu(self, P, table):
    '''
    Investissement en vue de la location meublée non professionnelle dans certains établissements ou résidences (case 7IJ)
    '''
    return zeros(self.taille)
    
def doment(self, P, table):
    '''
    Investissements dans les DOM-TOM dans le cadre d'une entrepise.
    '''
    UR = table.get('vous', 'f7ur', 'foy', 'foyer')
    OZ = table.get('vous', 'f7oz', 'foy', 'foyer')
    PZ = table.get('vous', 'f7pz', 'foy', 'foyer')
    QZ = table.get('vous', 'f7qz', 'foy', 'foyer')
    RZ = table.get('vous', 'f7rz', 'foy', 'foyer')
    SZ = table.get('vous', 'f7sz', 'foy', 'foyer')
    return  UR+ OZ + PZ +  QZ + RZ + SZ

def domsoc(self, P, table):
    '''
    Investissements outre-mer dans le logement social (déclaration n°2042 IOM)
    2010-
    '''
    return  zeros(self.taille)
