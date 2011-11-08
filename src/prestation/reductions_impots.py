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
    UD = table.getFoyer('vous', 'f7ud', 'foyer')
    return P.donapd.taux*minimum(UD, P.donapd.max)

def dfppce(self, P, table):   
    '''
    Dons aux autres oeuvres et dons effectués pour le financement des partis
    politiques et des compagnes électorales
    2002-
    '''
    base = table.getFoyer('vous', 'f7uf', 'foyer')
    if self.year >= 2004: base += table.getFoyer('vous', 'f7xs', 'foyer')
    if self.year >= 2005: base += table.getFoyer('vous', 'f7xt', 'foyer')
    if self.year >= 2006: base += table.getFoyer('vous', 'f7xu', 'foyer')
    if self.year >= 2007: base += table.getFoyer('vous', 'f7xw', 'foyer')
    if self.year >= 2008: base += table.getFoyer('vous', 'f7xy', 'foyer')
    max1 = P.dfppce.max*self.rbg_int
    return P.dfppce.taux*minimum(base, max1)
    # TODO: note de bas de page

def cotsyn(self, P, table):
    '''
    Cotisations syndicales
    2002-
    '''
    tx = P.cotsyn.seuil
    
    salv, salc, salp = table.getFoyer(['vous', 'conj',  'pac1'], 'sal')
    chov, choc, chop = table.getFoyer(['vous', 'conj',  'pac1'], 'cho')
    rstv, rstc, rstp = table.getFoyer(['vous', 'conj',  'pac1'], 'rst')
    maxv = (salv+chov+rstv)*tx
    maxc = (salc+choc+rstc)*tx
    maxp = (salp+chop+rstp)*tx
    
    AC = table.getFoyer('vous', 'f7ac', 'foyer')
    AE = table.getFoyer('vous', 'f7ae', 'foyer') 
    AG = table.getFoyer('vous', 'f7ag', 'foyer')
    return P.cotsyn.taux*(minimum(AC,maxv)  + minimum(AE,maxc) + minimum(AG,maxp))

def resimm(self, P, table):
    '''
    Travaux de restauration immobilière (cases 7RA et 7RB)
    2009-
    '''
    RA = table.getFoyer('vous', 'f7ra', 'foyer')
    RB = table.getFoyer('vous', 'f7rb', 'foyer')
    max1 = P.resimm.max
    max2 = maximum(max1 - RB, 0)
    return P.resimm.taux_rb*minimum(RB, max1)+ P.resimm.taux_ra*minimum(RA, max2)

def patnat(self, P, table):
    '''
    Dépenses de protections du patrimoine naturel (case 7KA)
    2010-
    '''
    KA = table.getFoyer('vous', 'f7ka', 'foyer')
    max1 = P.patnat.max
    return P.patnat.taux*minimum(KA, max1)

def sofipe(self, P, table):
    '''
    Souscription au capital d’une SOFIPECHE (case 7GS)
    2009-
    '''
    GS = table.getFoyer('vous', 'f7gs', 'foyer')
    max1 = minimum(P.sofipe.max*(self.marpac+1), P.sofipe.base*self.rbg_int) # page3 ligne 18
    return P.sofipe.taux*minimum(GS, max1)

def ecodev(self, P, table):
    '''
    Sommes versées sur un compte épargne codéveloppement (case 7UH)
    2009
    '''
    UH = table.getFoyer('vous', 'f7uh', 'foyer')
    return minimum(UH, minimum(P.ecodev.base*self.rbg_int, P.ecodev.max)) # page3 ligne 18

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
    DF = table.getFoyer('vous', 'f7df', 'foyer')
    DG = table.getFoyer('vous', 'f7dg', 'foyer')
    isinvalid = DG
    
    if self.year in (2002, 2003, 2004):
        max1 = P.saldom.max1*lnot(isinvalid) + P.saldom.max3*isinvalid
    elif self.year in (2005,2006):
        DL = table.getFoyer('vous', 'f7dl', 'foyer')
        nbpacmin = self.nbF + self.nbH/2 + self.nbJ + self.nbN + DL
        maxBase = P.saldom.max1
        maxDuMaxNonInv = P.saldom.max2
        maxNonInv = minimum(maxBase + P.saldom.pac*nbpacmin, maxDuMaxNonInv)
        max1 = maxNonInv*lnot(isinvalid) + P.saldom.max3*isinvalid
                 
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
                
    return P.saldom.taux*minimum(DF, max1)

def intagr(self, P, table):
    '''
    Intérêts pour paiement différé accordé aux agriculteurs
    2005-
    '''
    UM = table.getFoyer('vous', 'f7um', 'foyer')
    max1 = P.intagr.max*(1+self.marpac)
    return P.intagr.taux*minimum(UM, max1)

def prcomp(self, P, table):
    '''
    Prestations compensatoires
    2002-2010
    '''
    WM = table.getFoyer('vous', 'f7wm', 'foyer')
    WN = table.getFoyer('vous', 'f7wn', 'foyer')
    WO = table.getFoyer('vous', 'f7wo', 'foyer')
    WP = table.getFoyer('vous', 'f7wp', 'foyer')
    
    div = (WO==0)*1 + WO # Pour éviter les divisions par zéro
    
    return ((WM == 0)*((WN==WO)*P.prcomp.taux*minimum(WN,P.prcomp.seuil) +
                              (WN<WO)*(WO<=P.prcomp.seuil)*P.prcomp.taux*WN +
                              maximum(0,(WN<WO)*(WO> P.prcomp.seuil)*P.prcomp.taux*P.prcomp.seuil*WN/div) +
                              P.prcomp.taux*WP ) +
            (WM != 0)*((WN==WM)*(WO<=P.prcomp.seuil)*P.prcomp.taux*WM + 
                              maximum(0,(WN==WM)*(WO>=P.prcomp.seuil)*P.prcomp.taux*WM/div) + 
                              (WN>WM)*(WO<=P.prcomp.seuil)*P.prcomp.taux*WN  + 
                              maximum(0,(WN>WM)*(WO>=P.prcomp.seuil)*P.prcomp.taux*WN/div)) +
             P.prcomp.taux*WP)

def spfcpi(self, P, table):
    '''
    Souscription de parts de fonds communs de placement dans l'innovation, 
    de fonds d'investissement de proximité
    2002-
    '''
    max1 = P.spfcpi.max*(self.marpac+1)
    GQ = table.getFoyer('vous', 'f7gq', 'foyer')

    if self.year <= 2002:
        return P.spfcpi.taux1*minimum(GQ, max1)
    elif self.year <= 2006:
        FQ = table.getFoyer('vous', 'f7fq', 'foyer')
        return (P.spfcpi.taux1*minimum(GQ, max1) + 
                P.spfcpi.taux1*minimum(FQ, max1) )
    elif self.year <= 2010:
        FQ = table.getFoyer('vous', 'f7fq', 'foyer')
        FM = table.getFoyer('vous', 'f7fm', 'foyer')
        return (P.spfcpi.taux1*minimum(GQ, max1) + 
                P.spfcpi.taux1*minimum(FQ, max1) +
                P.spfcpi.taux2*minimum(FM, max1) )

def mohist(self, P, table):
    '''
    Travaux de conservation et de restauration d’objets classés monuments historiques (case NZ)
    2008-
    '''
    NZ = table.getFoyer('vous', 'f7nz', 'foyer')
    return P.mohist.taux*minimum(NZ, P.mohist.max)

def sofica(self, P, table):
    '''
    Souscriptions au capital de SOFICA
    2006-
    '''
    GN = table.getFoyer('vous', 'f7gn', 'foyer')
    FN = table.getFoyer('vous', 'f7fn', 'foyer')
    max0 = minimum(P.sofica.taux1*maximum(self.rng,0), P.sofica.max)
    max1 = minimum(0, max0 - GN)
    return P.sofica.taux2*minimum(GN, max0) + \
           P.sofica.taux3*minimum(FN, max1)

def cappme(self, P, table):
    '''
    Souscriptions au capital des PME
    2002-
    '''
    base = table.getFoyer('vous', 'f7cf', 'foyer')
    if self.year >= 2003: base += table.getFoyer('vous', 'f7cl', 'foyer')
    if self.year >= 2004: base += table.getFoyer('vous', 'f7cm', 'foyer')
    if self.year >= 2005: base += table.getFoyer('vous', 'f7cn', 'foyer')
    seuil = P.cappme.seuil*(self.marpac + 1)

    if self.year <= 2008:
        return P.cappme.taux*minimum(base,seuil)
    elif self.year <= 2010:
        CU = table.getFoyer('vous', 'f7cu', 'foyer')
        seuil_tpe = P.cappme.seuil_tpe*(self.marpac + 1)
        return P.cappme.taux*(minimum(base,seuil)+minimum(CU, seuil_tpe))

def intemp(self, P, table):
    '''
    Intérêts d'emprunts
    2002-2003
    '''
    WG = table.getFoyer('vous', 'f7wg', 'foyer')
    max1 = P.intemp.max + P.intemp.pac*self.nbPAC
    return P.intemp.taux*minimum(WG, max1)

def intcon(self, P, table):
    '''
    Intérêts des prêts à la consommation (case UH)
    2004-2005
    '''
    max1 = P.intcon.max
    UH = table.getFoyer('vous', 'f7uh', 'foyer')
    return P.intcon.taux*minimum(UH, max1)

def repsoc(self, P, table):
    '''
    Intérèts d'emprunts pour reprises de société
    '''
    FH = table.getFoyer('vous', 'f7fh', 'foyer')
    seuil = P.repsoc.seuil*(self.marpac+1)
    return P.repsoc.taux*minimum(FH, seuil)
    
def invfor(self, P, table):
    '''
    Investissements forestiers
    '''
    UN = table.getFoyer('vous', 'f7un', 'foyer')
    if self.year <= 2002:
        seuil = P.invfor.seuil*(self.marpac + 1)
        return P.invfor.taux*minimum(UN, seuil)
    elif self.year <= 2008:
        return P.invfor.taux*UN
    else:
        seuil = 0 # vérifier la notice à partir de 2009
        return P.invfor.taux*minimum(UN, seuil) 

def garext(self, P, table):
    '''
    Frais de garde des enfants à l’extérieur du domicile (cases GA, GB, GC de la 2042)
    et GE, GF, GG
    2002-2005
    '''
    max1 = P.garext.max 
    GA = table.getFoyer('vous', 'f7ga', 'foyer')
    GB = table.getFoyer('vous', 'f7gb', 'foyer')
    GC = table.getFoyer('vous', 'f7gc', 'foyer')
    if self.year <= 2002:
        return P.garext.taux*(minimum(GA, max1) + 
                              minimum(GB, max1) + 
                              minimum(GC, max1) )
    elif self.year <= 2005:
        GE = table.getFoyer('vous', 'f7ge', 'foyer')
        GF = table.getFoyer('vous', 'f7gf', 'foyer')
        GG = table.getFoyer('vous', 'f7gg', 'foyer')
        return P.garext.taux*(minimum(GA, max1) + 
                              minimum(GB, max1) + 
                              minimum(GC, max1) + 
                              minimum(GE, max1/2) + 
                              minimum(GF, max1/2) + 
                              minimum(GG, max1/2) )

def deffor(self, P, table):
    '''
    Défense des forêts contre l'incendie
    '''
    UC = table.getFoyer('vous', 'f7uc', 'foyer')
    return P.deffor.taux*minimum(UC, P.deffor.max )
    
def daepad(self, P, table):
    '''
    Dépenses d'accueil dans un établissement pour personnes âgées dépendantes
    '''
    CD = table.getFoyer('vous', 'f7cd', 'foyer')
    CE = table.getFoyer('vous', 'f7ce', 'foyer')
    return P.daepad.taux*(minimum(CD, P.daepad.max) + minimum(CE, P.daepad.max))

def rsceha(self, P, table):
    '''
    Rentes de survie et contrats d'épargne handicap
    '''
    GZ = table.getFoyer('vous', 'f7gz', 'foyer')
    max1 = P.rsceha.seuil1 + (self.nbPAC - self.nbR + self.nbH/2)*P.rsceha.seuil2
    # TODO: verifier la formule précédente
    return P.rsceha.taux*minimum(GZ, max1)

def assvie(self, P, table):
    '''
    Assurance-vie (cases GW, GX et GY de la 2042)
    2002-2004
    '''
    GW = table.getFoyer('vous', 'f7gw', 'foyer')
    GX = table.getFoyer('vous', 'f7gx', 'foyer')
    GY = table.getFoyer('vous', 'f7gy', 'foyer')
    max1 = P.assvie.max + self.nbPAC*P.assvie.pac
    return P.assvie.taux*minimum(GW + GX + GY, max1)

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
    XC = table.getFoyer('vous', 'f7xc', 'foyer')
    if self.year == 2004: xc = P.invlst.taux_xc*minimum(XC,seuil1/4)
    else: xc = P.invlst.taux_xc*minimum(XC,seuil1/6)
    xd = P.invlst.taux_xd*table.getFoyer('vous', 'f7xd', 'foyer')
    xe = P.invlst.taux_xe*minimum(table.getFoyer('vous', 'f7xe', 'foyer'),seuil1/6)
    xf = P.invlst.taux_xf*table.getFoyer('vous', 'f7xf', 'foyer')
    xg = P.invlst.taux_xg*minimum(table.getFoyer('vous', 'f7xg', 'foyer'),seuil2)
    xh = P.invlst.taux_xh*minimum(table.getFoyer('vous', 'f7xh', 'foyer'), seuil3)
    xi = P.invlst.taux_xi*minimum(table.getFoyer('vous', 'f7xi', 'foyer'), seuil1/4)
    xj = P.invlst.taux_xj*table.getFoyer('vous', 'f7xj', 'foyer')
    xk = P.invlst.taux_xk*table.getFoyer('vous', 'f7xk', 'foyer')
    xl = P.invlst.taux_xl*minimum(table.getFoyer('vous', 'f7xl', 'foyer'), seuil1/6)
    xm = P.invlst.taux_xm*table.getFoyer('vous', 'f7xm', 'foyer')
    xn = P.invlst.taux_xn*minimum(table.getFoyer('vous', 'f7xn', 'foyer'),seuil1/6)
    xo = P.invlst.taux_xo*table.getFoyer('vous', 'f7xo', 'foyer')
    return xc + xd + xe + xf + xg + xh + xi + xj + xk + xl + xm + xn + xo
    
def domlog(self, P, table):
    '''
    Investissements OUTRE-MER dans le secteur du logement et autres secteurs d’activité
    2002-2009
    TODO: Plafonnement sur la notice
    '''
    if self.year <= 2002:
        UA = table.getFoyer('vous', 'f7ua', 'foyer')
        UB = table.getFoyer('vous', 'f7ub', 'foyer')
        UC = table.getFoyer('vous', 'f7uc', 'foyer')
        UJ = table.getFoyer('vous', 'f7uj', 'foyer')    
        return P.domlog.taux1*UJ + P.domlog.taux2*(UA + UB + UC) 
    if self.year <= 2004:
        UA = table.getFoyer('vous', 'f7ua', 'foyer')
        UB = table.getFoyer('vous', 'f7ub', 'foyer')
        UC = table.getFoyer('vous', 'f7uc', 'foyer')
        UI = table.getFoyer('vous', 'f7ui', 'foyer')
        UJ = table.getFoyer('vous', 'f7uj', 'foyer')
        return P.domlog.taux1*UJ + P.domlog.taux2*(UA + UB + UC) + UI
    elif self.year <= 2007:
        UA = table.getFoyer('vous', 'f7ua', 'foyer')
        UB = table.getFoyer('vous', 'f7ub', 'foyer')
        UI = table.getFoyer('vous', 'f7ui', 'foyer')
        UJ = table.getFoyer('vous', 'f7uj', 'foyer')
        return P.domlog.taux1*UJ + P.domlog.taux2*(UA + UB ) + UI
    elif self.year <= 2008:
        UI = table.getFoyer('vous', 'f7ui', 'foyer')    
        return UI
    elif self.year <= 2009:
        QB = table.getFoyer('vous', 'f7qb', 'foyer')
        QC = table.getFoyer('vous', 'f7qc', 'foyer')
        QD = table.getFoyer('vous', 'f7qd', 'foyer')
        return QB + QC + QD
    elif self.year <= 2010:
        QB = table.getFoyer('vous', 'f7qb', 'foyer')
        QC = table.getFoyer('vous', 'f7qc', 'foyer')
        QL = table.getFoyer('vous', 'f7ql', 'foyer')
        QT = table.getFoyer('vous', 'f7qt', 'foyer')
        QM = table.getFoyer('vous', 'f7qm', 'foyer')
        QD = table.getFoyer('vous', 'f7qd', 'foyer')
        return QB + QC + QL + QT + QM + QD
 
def adhcga(self, P, table):
    '''
    Frais de comptabilité et d'adhésion à un CGA ou AA
    2002-
    '''
    FF = table.getFoyer('vous', 'f7ff', 'foyer')
    FG = table.getFoyer('vous', 'f7fg', 'foyer')
    return minimum(FF, P.adhcga.max*FG)

def creaen(self, P, table):
    '''
    Aide aux créateurs et repreneurs d'entreprises
    TODO...
    '''
    if self.year <= 2008:
        FY = table.getFoyer('vous', 'f7fy', 'foyer')
        GY = table.getFoyer('vous', 'f7gy', 'foyer')
        return (P.creaen.base*FY + P.creaen.hand*GY )
    elif self.year == 2009:
        JY = table.getFoyer('vous', 'f7jy', 'foyer')
        FY = table.getFoyer('vous', 'f7fy', 'foyer')
        HY = table.getFoyer('vous', 'f7hy', 'foyer')
        KY = table.getFoyer('vous', 'f7ky', 'foyer')
        GY = table.getFoyer('vous', 'f7gy', 'foyer')
        IY = table.getFoyer('vous', 'f7iy', 'foyer')
        return (P.creaen.base*((JY + FY) + HY/2) +
                P.creaen.hand*((KY + GY) + IY/2) )
    elif self.year == 2010:
        JY = table.getFoyer('vous', 'f7jy', 'foyer')
        FY = table.getFoyer('vous', 'f7fy', 'foyer')
        HY = table.getFoyer('vous', 'f7hy', 'foyer')
        LY = table.getFoyer('vous', 'f7ly', 'foyer')
        KY = table.getFoyer('vous', 'f7ky', 'foyer')
        GY = table.getFoyer('vous', 'f7gy', 'foyer')
        IY = table.getFoyer('vous', 'f7iy', 'foyer')
        MY = table.getFoyer('vous', 'f7my', 'foyer')
        return (P.creaen.base*((JY + FY) + (HY + LY)/2) +
                P.creaen.hand*((KY + GY) + (IY + MY)/2) )
      
def ecpess(self, P, table):
    '''
    Enfants à charge poursuivant leurs études secondaires ou supérieures
    '''
    EA = table.getFoyer('vous', 'f7ea', 'foyer')
    EB = table.getFoyer('vous', 'f7eb', 'foyer')
    EC = table.getFoyer('vous', 'f7ec', 'foyer')
    ED = table.getFoyer('vous', 'f7ed', 'foyer')
    EF = table.getFoyer('vous', 'f7ef', 'foyer')
    EG = table.getFoyer('vous', 'f7eg', 'foyer')
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
    UR = table.getFoyer('vous', 'f7ur', 'foyer')
    OZ = table.getFoyer('vous', 'f7oz', 'foyer')
    PZ = table.getFoyer('vous', 'f7pz', 'foyer')
    QZ = table.getFoyer('vous', 'f7qz', 'foyer')
    RZ = table.getFoyer('vous', 'f7rz', 'foyer')
    SZ = table.getFoyer('vous', 'f7sz', 'foyer')
    return  UR+ OZ + PZ +  QZ + RZ + SZ

def domsoc(self, P, table):
    '''
    Investissements outre-mer dans le logement social (déclaration n°2042 IOM)
    2010-
    '''
    return  zeros(self.taille)
