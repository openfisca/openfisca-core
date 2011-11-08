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
from numpy import maximum as maxi
from numpy import minimum as mini
from numpy import logical_xor as lxor
from numpy import logical_not as lnot
import re
import numpy as np
from numpy import round, zeros, ones
from Utils import BarmMar
import charges_deductibles
import reductions_impots
import credits_impots

# TODO: Les revenus d'heures supplémentaires exonérés et le RSA perçu du ménage...

class IRPP(object):
    '''
    objet contenant la table foyer et les methodes associées
    '''
    def __init__(self, table):
        super(IRPP,self).__init__()
        '''
        Constructor
        '''
        self.population = table
        self.declVar = table.scenario.declar
        self.taille = self.population.nbFoy
        self.year   = self.population.year
        self.scenar2foy = self.population.scenar2foy
        self.people = ['vous','conj','pac1','pac2','pac3']
        self._createFoyer(table)
        
#    def __getattribute__(self, name):
#        '''
#        The getattribute special method generate a zeros vector if the requested name
#        is a cell of the declaration and does not exist. 
#        '''
#        try:
#            return super(IRPP, self).__getattribute__(name)
#        except:
#            if re.match(r'^f\d[a-z]{2}$', name):
#                return zeros(self.taille)
#            else:
#                return super(IRPP, self).__getattribute__(name)
        
    def _createFoyer(self, table):
        table.openReadMode()
        cases = ['caseK', 'caseE', 'caseH', 'caseN', 'caseL', 'caseP', 
                 'caseF', 'caseW', 'caseS', 'caseG', 'caseT',
                 'nbF', 'nbH', 'nbG', 'nbI', 'nbR', 'nbJ', 'nbN']
        for case in cases:
            setattr(self, case, table.getFoyer('vous', case, 'foyer'))

        table.close_()
                
    def _retrieveIndiv(self, table):

        table.openReadMode()
        # On récupère l'âge au premier janvier du déclarant et de son conjoint
        self.agev, self.agec = table.getFoyer(['vous', 'conj'], 'age')

        
        # On récupère le statut marital
        self.statmarit = table.getFoyer('vous', 'statmarit')

        self.marpac = (self.statmarit == 1) | (self.statmarit == 5)
        self.celdiv = (self.statmarit == 2) | (self.statmarit == 3)
        self.veuf   =  self.statmarit == 4
        
        self.nbadult = 2*self.marpac + 1*(self.celdiv | self.veuf)

        self.zglof = self.Glo(table)
        table.close_()
        
        table.openWriteMode()

        #2 Revenus des valeurs et capitaux mobiliers
        # gains de levée d'options du foyer
        table.setColl('glo',self.zglof)
        # TODO : ty ? uy ?

        # Revenus d'activité imposés au quotient
#        zquof = self.f0xx
#        table.setColl('quo', zquof)

        # Revenus de l'étranger
        self.zetrf = zeros(self.taille)
#        self.zetrf = self.f8ti + self.f1dy + self.f1ey
#        table.setColl('etr', self.zetrf)

        self.jveuf = zeros(self.taille, dtype = bool)
        self.jourXYZ = 360*ones(self.taille)

        table.close_()

    def IR(self,P):
        '''
        Calcul de l'impôt sur le revenu
        '''
        table = self.population
        table.openReadMode()
        GH = table.getFoyer('vous', 'f6gh', 'foyer')
        DE = table.getFoyer('vous', 'f6de', 'foyer')
        VA = table.getFoyer('vous', 'f3va', 'foyer')
        VC = table.getFoyer('vous', 'f3vc', 'foyer')
        VE = table.getFoyer('vous', 'f3ve', 'foyer')
        VG = table.getFoyer('vous', 'f3vg', 'foyer')
        VH = table.getFoyer('vous', 'f3vh', 'foyer')
        VL = table.getFoyer('vous', 'f3vl', 'foyer')
        VM = table.getFoyer('vous', 'f3vm', 'foyer')
        BL = table.getFoyer('vous', 'f4bl', 'foyer')
        QM = table.getFoyer('vous', 'f5qm', 'foyer')
        RM = table.getFoyer('vous', 'f5rm', 'foyer')
        GA = table.getFoyer('vous', 'f7ga', 'foyer')
        GB = table.getFoyer('vous', 'f7gb', 'foyer')
        GC = table.getFoyer('vous', 'f7gc', 'foyer')
        table.close_()
        self._retrieveIndiv(table)

        self.nbPAC = self.nbF + P.autre.D_enfJ*(self.nbJ) + self.nbR
        
        alloc = self.Alloc(P.autre, table)
        
        ## Revenus categoriels
        TSPR, RVCM, RFON, RPNS = self.RevCat(P)
        
        ## Nombre de part
        self.nbptr = self.Nbpt(P.quotient_familial)

        ## Déficits antérieurs
        deficitAnte = self.Deficit_anterieur()

        # sans les revenus au quotient ;
        ## Total 17 - Revenu brut global
        self.rbg = maxi(0, alloc + TSPR + RVCM + RFON + RPNS + GH - deficitAnte)

        ## CSG déductible
        self.CSGdeduc = mini(DE, maxi(self.rbg, 0))
        ## Charges déductibles
        self.Charges_deductibles(P.charges_deductibles)

        ## Total 20 - Revenu net global
        self.rng = maxi(0, self.rbg - self.CSGdeduc - self.CD)
        
        ## Abattements spéciaux        
        abaspe = self.Abattements(P.abattements_speciaux, self.rng)
    
        ## Revenu net imposable
        rni = self.rng - abaspe
        self.revimp = rni

        ## Nature d'imposition
        natimp = self.Non_imposabilite(rni, self.nbptr, P.non_imposable)

        ## calul de l'impôt sur le revenu
        self.IR_brut = self.nbptr*BarmMar(rni/self.nbptr, P.bareme) # TODO : partir d'ici, petite différence avec Matlab

        # Impôt après plafonnement du QF et réductions post-plafond
        IP = self.PlafQf(P)

        ## Droit simple sur les revenus au quotient
        mnirqu = zeros(self.taille); # TODO :
        # self.mnirqu = (self.IP1-self.IP0)*4; # TODO
        # self.IP = self.IP0 + self.mnirqu

        ## Décote
        decote = self.Decote(IP, P.decote)
        IPnet  = natimp*maxi(0, IP - decote)
        
#        t = (1 - P.tspr.abatpro.taux)
#        ## Revenus de l'étranger pour le revenu fiscal de référence
#        rfr_ertf = self.f8by + self.f8cy + t*self.f1dy  + maxi(self.f8ti, t*(self.f1lz + self.f1mz))
        
        ## Revenu fiscal de référence
        # les allocations familiales ne sont pas prises en compte pour le revenu fiscal de référence si elles sont imposables
        self.rfr = (maxi(0, rni - alloc) + self.rfr_cd + self.rfr_rvcm + self.rfr_glof + self.rpns_exo + self.rpns_pvce + VA + VG)
#        self.rfr = (self.f8fv==0)*(maxi(0, rni - alloc) + self.rfr_cd + rfr_ertf + self.rfr_rvcm + self.rfr_glof + self.rpns_exo + self.rpns_pvce + VA + VG)
        tehr = self.Tehr(self.rfr, self.nbadult, P.tehr)
        ## Réduction d'impôt
        reductions = self.Reductions(IPnet, P.reductions_impots, table)
     
        # impot après imputation des réductions d'impôt
        iaidrdi  = IPnet - reductions

        ## 9. Impôt à payer 
        # Impôt sur les plus values à taux forfaitaires (16%, 22.5%, 30%, 40%)
        mnirvp = self.Plus_values(P.plus_values, table)
    
        # TODO : contribution sur les revenus locatifs
        P.loyf_taux = 0.025
        P.loyf_seuil = 0
        G90 = round(P.loyf_taux *(BL >= P.loyf_seuil)*BL)
        mnclcn = G90 
        zimployf = mnclcn

        # Taxe exceptionelle sur l'indemnité compensatrice des agents d'assurance
        #     H90_a1 = 0*maxi(0,mini(self.f5qm,23000));
        H90_a2 = .04*maxi(0,mini(QM-23000,107000));
        H90_a3 = .026*maxi(0,QM-107000);
        #     H90_b1 = 0*maxi(0,mini(self.f5rm,23000));
        H90_b2 = .04*maxi(0,mini(RM-23000,107000));
        H90_b3 = .026*maxi(0,RM-107000);
        
        H90 = H90_a2 + H90_a3 + H90_b2 + H90_b3;

        #  impôt avant imputation     
        iai = iaidrdi + mnirvp + G90 + H90
        
        # Reprise du crédit d'impôt en faveur des jeunes, des accomptes et des versements mensues de prime pour l'emploi
        reprise = zeros(self.taille) # TODO : self.reprise=J80;

        Pcredit = P.credits_impots
        if hasattr(P.reductions_impots,'saldom'): Pcredit.saldom =  P.reductions_impots.saldom
        credits_impot = self.Credits(Pcredit, table)
        
        # Montant avant seuil de recouvrement
        IMP = iai - credits_impot + tehr
                            
        ## Crédit d'impôt revenu de l'étranger
#        abaetr = round(mini(maxi(P.tspr.abatpro.taux*self.f8tk, P.tspr.abatpro.min),P.tspr.abatpro.max))
#        saletr = self.f8tk - abaetr
#        div = rni + (rni == 0)
#        credimp_etranger = maxi(0,saletr/div)*iaidrdi
                
        # Les variables d'impôts directs 
        # impôt sur le revenu
        mcirra = -((IMP<=-8)*IMP)
        mciria = maxi(0,(IMP>=0)*IMP - zimployf)
#        mciria = maxi(0,(IMP>=0)*IMP - credimp_etranger - zimployf - ( self.f8to + self.f8tb + self.f8tc ))
        
        # Dans l'ERFS, les prelevement libératoire sur les montants non déclarés
        # sont intégrés. Pas possible de le recalculer.
        
        table.openWriteMode()


        # impot sur le revenu du foyer (hors prélèvement libératoire, revenus au quotient)
        irpp   = -(mciria + self.ppetot - mcirra - mnirvp - mnirqu)
        table.setColl('irpp', irpp)

        impforf = mnirvp + mnirqu
        
        # TODO: La taxe d'habitation
        thab = - zeros(self.taille)
        table.setColl('thab', thab)
        
        zdivf = VC + VE + VG - VH + VL + VM \
              + self.rpns_pvce + self.rpns_pvct - self.rpns_mvct - self.rpns_mvlt
        
        table.setColl('div', zdivf)

        zdiv_rmi = VC + VE + VG + VL + VM
        
        table.setColl('div_rmi', zdiv_rmi)

        revColl = self.tspre + self.rvcme + self.zetrf*0.9 + self.zfonf + zdivf + self.zglof - self.zalvf - GA - GB - GC - abaspe
        table.setColl('revColl', revColl)
        
        # pour le calcul de l'allocation de soutien familial     
        asf_elig = 1*(self.caseT | self.caseL)
        table.setFoyer('vous','asf_elig', asf_elig)
        
        table.setFoyer('vous','al_nbinv', self.nbR)
        
        table.close_()

    def Tehr(self, rfr, nbadult, P):
        return BarmMar(rfr/nbadult, P)*nbadult

    def Glo(self, table):
        '''
        Gains de levée d'option
        '''
        f1tv = table.getFoyer('vous', 'f1tv', 'foyer')
        f1tw = table.getFoyer('vous', 'f1tw', 'foyer')
        f1tx = table.getFoyer('vous', 'f1tx', 'foyer')
        f1uv = table.getFoyer('vous', 'f1uv', 'foyer')
        f1uw = table.getFoyer('vous', 'f1uw', 'foyer')
        f1ux = table.getFoyer('vous', 'f1ux', 'foyer')
        f3vf = table.getFoyer('vous', 'f3vf', 'foyer')
        f3vi = table.getFoyer('vous', 'f3vi', 'foyer')
        f3vj = table.getFoyer('vous', 'f3vj', 'foyer')
        f3vk = table.getFoyer('vous', 'f3vk', 'foyer')
        return f1tv + f1tw + f1tx + f1uv + f1uw + f1ux + f3vf + f3vi + f3vj + f3vk                   

    def Alloc(self,P, table):
        '''
        ALLOCATION FAMILLIALE IMPOSABLE
        '''
        if P.alloc_imp:
            # On récupère les allocations familiales perçues par les membres du foyer
            table.openReadMode()
            temp = table.getFoyer(self.people, 'af', sumqui = True)
            table.close_()
            return temp
        else:
            return zeros(self.taille)

    
    ## Cacul des revenu catégoriel
    def Tspr(self, P, table):
        '''
        TRAITEMENTS SALAIRES PENSIONS ET RENTES
        '''
        table.openReadMode()         
        AJ, BJ, CJ, DJ, EJ = table.getFoyer(self.people, 'sal')
        AI, BI, CI, DI, EI = table.getFoyer(self.people, 'choCheckBox')
        AP, BP, CP, DP, EP = table.getFoyer(self.people, 'cho')
        AS, BS, CS, DS, ES = table.getFoyer(self.people, 'rst')
        AK, BK, CK, DK, EK = table.getFoyer(self.people, 'fra')
        AO, BO, CO, DO, EO = table.getFoyer(self.people, 'alr')
        AU, BU, CU, DU, EU = table.getFoyer(self.people, 'hsup')
        AW = table.getFoyer('vous', 'f1aw', 'foyer')
        BW = table.getFoyer('vous', 'f1bw', 'foyer')
        CW = table.getFoyer('vous', 'f1cw', 'foyer')
        DW = table.getFoyer('vous', 'f1dw', 'foyer')
        VJ = table.getFoyer('vous', 'f3vj', 'foyer')
        VK = table.getFoyer('vous', 'f3vk', 'foyer')
        table.close_()        

        def salnet(dumchom, revsal, fraispro, P):
            amin = P.min*lnot(dumchom) + P.min2*dumchom
            abatfor = round(mini(maxi(P.taux*revsal, amin),P.max))
            return (fraispro > abatfor)*(revsal - fraispro) \
                 + (fraispro <= abatfor)*maxi(0,revsal - abatfor)

        def pennet(pen, P):
            return maxi(0, pen - round(maxi(P.taux*pen , P.min)))
                        
        salv = salnet(AI, AJ + AP + VJ, AK, P.abatpro)
        salc = salnet(BI, BJ + BP + VK, BK, P.abatpro)
        sal1 = salnet(CI, CJ + CP     , CK, P.abatpro)
        sal2 = salnet(DI, DJ + DP     , DK, P.abatpro)
        sal3 = salnet(EI, EJ + EP     , EK, P.abatpro)
        
        penv = pennet(AS + AO, P.abatpen)
        penc = pennet(BS + BO, P.abatpen)
        pen1 = pennet(CS + CO, P.abatpen)
        pen2 = pennet(DS + DO, P.abatpen)
        pen3 = pennet(ES + EO, P.abatpen)
        
        f11 = penv + penc + pen1 + pen2 + pen3 
        
        #problème car les pensions sont majorées au niveau du foyer
        d11 = ( AS + BS + CS + DS + ES + 
                AO + BO + CO + DO + EO ) 
        
        penv2 = (d11-f11> P.abatpen.max)*(penv + (d11-f11-P.abatpen.max)) + (d11-f11<= P.abatpen.max)*penv
        
        # Plus d'abatement de 20% en 2006
        salpenv2 = salv + penv2
        salpenv  = salv + penv
        salpenc  = salc + penc
        salpen1  = sal1 + pen1
        salpen2  = sal2 + pen2
        salpen3  = sal3 + pen3
        
        h11 = salpenv2 + salpenc + salpen1 + salpen2 + salpen3
        # voir foyers 16 et 29006 pour comprendre?
        tot1 = round(h11)
        # rentes viagères à titre onéreux
        rto = AW + BW + CW + DW
        tot2 = round(P.abatviag.taux1*AW + 
                     P.abatviag.taux2*BW + 
                     P.abatviag.taux3*CW + 
                     P.abatviag.taux4*DW)
        
        table.openWriteMode()
        table.setFoyer('vous', 'tspr', salpenv)
        table.setFoyer('conj', 'tspr', salpenc)
        table.setFoyer('pac1', 'tspr', salpen1)
        table.setFoyer('pac2', 'tspr', salpen2)
        table.setFoyer('pac3', 'tspr', salpen3)
        table.setFoyer('vous', 'rto', rto)
        table.close_()

        self.tspre = tot2
        return tot1 + tot2

    def Rvcm(self, P, table):
        '''
        REVENUS DES VALEURS ET CAPITAUX MOBILIERS
        '''
        table.openReadMode()
        CH = table.getFoyer('vous', 'f2ch', 'foyer')
        DC = table.getFoyer('vous', 'f2dc', 'foyer')
        TS = table.getFoyer('vous', 'f2ts', 'foyer')
        CA = table.getFoyer('vous', 'f2ca', 'foyer')
        FU = table.getFoyer('vous', 'f2fu', 'foyer')
        GO = table.getFoyer('vous', 'f2go', 'foyer')
        TR = table.getFoyer('vous', 'f2tr', 'foyer')
        AB = table.getFoyer('vous', 'f2ab', 'foyer')
        DA = table.getFoyer('vous', 'f2da', 'foyer')
        DH = table.getFoyer('vous', 'f2dh', 'foyer')
        EE = table.getFoyer('vous', 'f2ee', 'foyer')
        VI = table.getFoyer('vous', 'f3vi', 'foyer')
        AA = table.getFoyer('vous', 'f2aa', 'foyer')
        AL = table.getFoyer('vous', 'f2al', 'foyer')
        AM = table.getFoyer('vous', 'f2am', 'foyer')
        AN = table.getFoyer('vous', 'f2an', 'foyer')
        if self.year <= 2004: GR = table.getFoyer('vous', 'f2gr', 'foyer')
        else: GR = 0
        table.close_()

        ## Calcul du revenu catégoriel
        #1.2 Revenus des valeurs et capitaux mobiliers
        b12 = mini(CH,P.abat_assvie*(1+self.marpac))
        TOT1 = CH-b12
        # Part des frais s'imputant sur les revenus déclarés case DC
        den = ((DC + TS)!=0)*(DC + TS) + ((DC + TS)==0)
        F1 =  CA/den*DC
        
        # Revenus de capitaux mobiliers nets de frais, ouvrant droit à abattement
        # partie négative (à déduire des autres revenus nets de frais d'abattements
        g12a = - mini(DC*P.abatmob_taux - F1,0)
        # partie positive
        g12b = maxi(DC*P.abatmob_taux - F1,0)
        
        rev = g12b + GR + FU*P.abatmob_taux

        # Abattements, limité au revenu
        h12 = P.abatmob*(1+self.marpac)
        TOT2 = maxi(0,rev - h12)
        i121= -mini(0,rev - h12)
        
        # Pars des frais s'imputant sur les revenus déclarés ligne TS
        F2 = CA - F1
        TOT3 = (TS - F2) + GO*P.majGO + TR - g12a

        DEF = AA + AL + AM + AN

        RVCM = maxi(TOT1 + TOT2 + TOT3 - DEF, 0)
        
        # a. Les revenus des valeurs et capitaux mobiliers
        # a.(i) Les revenus non soumis au prélèvement libératoire (zvamf) " TODO : f2fu non compris car exonéré de contributions sociales?
        revcap_bar = DC + GR + CH + TS + GO + TR - AB + FU

        # a.(ii) Avoir fiscal et crédits d'impôt (zavff)
        avf = AB
        # a.(iii) Les revenus de valeurs mobilières soumis au prélèvement
        # libératoire (zvalf)
        if self.year <=2007: 
            revcap_lib = DH + EE
            imp_lib = - (P.prelevement_liberatoire.assvie*DH + 
                         P.prelevement_liberatoire.autre*EE )
        else:                
            revcap_lib = DA + DH + EE
            imp_lib = - (P.prelevement_liberatoire.action*DA + 
                         P.prelevement_liberatoire.assvie*DH + 
                         P.prelevement_liberatoire.autre*EE )

        self.rvcme = revcap_lib + revcap_bar
        table.openWriteMode()
        table.setColl('avf', avf)
        table.setColl('revcap_bar', revcap_bar)
        table.setColl('revcap_lib', revcap_lib)
        table.setColl('imp_lib', imp_lib)
        table.close_()
                
        ## pour le calcul du revenu fiscal de référence
        self.rfr_rvcm = maxi((1-P.abatmob_taux)*(DC + FU) - i121, 0) + revcap_lib
        self.rfr_glof = VI
        return RVCM

    def Rfon(self, P, table):
        '''
        REVENUS FONCIERS
        '''
        table.openReadMode()
        BA = table.getFoyer('vous', 'f4ba', 'foyer')
        BB = table.getFoyer('vous', 'f4bb', 'foyer')
        BC = table.getFoyer('vous', 'f4bc', 'foyer')
        BD = table.getFoyer('vous', 'f4bd', 'foyer')
        BE = table.getFoyer('vous', 'f4be', 'foyer')
        table.close_()
        
        ## Calcul des totaux        
        self.zfonf = BA - BB - BC + round(BE*(1-P.microfoncier.taux))  
        
        ## Calcul du revenu catégoriel
        a13 = BA + BE - P.microfoncier.taux*BE*(BE <= P.microfoncier.max)
        b13 = BB
        c13 = a13-b13
        d13 = BC
        e13 = c13- d13*(c13>=0)
        f13 = BD*(e13>=0)
        g13 = maxi(0, e13- f13)
        RFON  = (c13>=0)*(g13 + e13*(e13<0)) - (c13<0)*d13
        self.rfon_rmi = BA + BE

        table.openWriteMode()
        table.setColl('rfon',self.rfon_rmi)
        table.setColl('fon',self.zfonf)
        table.close_()

        return RFON

    def Rpns(self,P, table):
        n = self.taille
        self.rpns_pvce = np.zeros(n)
        # revenus exonérés
        self.rpns_exo =  np.zeros(n)
        self.zragf = np.zeros(n)
        self.zricf = np.zeros(n)
        self.zracf = np.zeros(n)
        self.zrncf = np.zeros(n)

        self.rpns_pvct = np.zeros(n)
        self.rpns_mvct = np.zeros(n)
        self.rpns_mvlt = np.zeros(n)
        
        # imp_plusval_ces = plusval_ces*plusvalces_taux;
        RPNS = np.zeros(n)
        
        # Calcul des revenus individuels
        self.rpnsv = np.zeros(n)
        self.rpnsc = np.zeros(n)
        self.rpnsp = np.zeros(n)
        
        return RPNS
        
    def Rpns_full(self, P, table):
        '''
        REVENUS DES PROFESSIONS NON SALARIEES
        partie 5 de la déclaration complémentaire
        '''

        def abatv(rev, P):
            return maxi(0,rev - mini(rev, maxi(P.microentreprise.vente_taux*mini(P.microentreprise.vente_max, rev), P.microentreprise.vente_min)))
        
        def abats(rev, P):
            return maxi(0,rev - mini(rev, maxi(P.microentreprise.servi_taux*mini(P.microentreprise.servi_max, rev), P.microentreprise.servi_min)))
        
        def abatnc(rev, P):
            return maxi(0,rev - mini(rev, maxi(P.nc_abat_taux*mini(P.nc_abat_max, rev), P.nc_abat_min)))


        def Pvce(self):
            ''' 
            Plus values de cession
            '''
            hx , ix , jx = self.f5hx , self.f5ix , self.f5jx
            he , ie , je = self.f5he , self.f5ie , self.f5je
            hk , ik , jk = self.f5hk , self.f5ik , self.f5jk
            kq , lq , mq = self.f5kq , self.f5lq , self.f5mq
            ke , le , me = self.f5ke , self.f5le , self.f5me
            kk , lk , mk = self.f5kk , self.f5lk , self.f5mk
            nq , oq , pq = self.f5nq , self.f5oq , self.f5pq
            ne , oe , pe = self.f5ne , self.f5oe , self.f5pe
            nk , ok , pk = self.f5nk , self.f5ok , self.f5pk
            kv , lv , mv = self.f5kv , self.f5lv , self.f5mv
            so , nt , ot = self.f5so , self.f5nt , self.f5ot
            hr , ir , jr = self.f5hr , self.f5ir , self.f5jr
            qd , rd , sd = self.f5qd , self.f5rd , self.f5sd
            qj , rj , sj = self.f5qj , self.f5rj , self.f5sj 

            fragf = hx + ix + jx
            aragf = he + ie + je
            nragf = hk + ik + jk
            mbicf = kq + lq + mq
            abicf = ke + le + me
            nbicf = kk + lk + mk
            maccf = nq + oq + pq
            aaccf = ne + oe + pe
            naccf = nk + ok + pk
            mncnp = kv + lv + mv
            cncnp = so + nt + ot
            mbncf = hr + ir + jr
            abncf = qd + rd + sd
            nbncf = qj + rj + sj

            return ( fragf + aragf + nragf + mbicf + abicf + 
                     nbicf + maccf + aaccf + naccf + mbncf + 
                     abncf + nbncf + mncnp + cncnp )

        def Exon(self):
            ''' 
            Plus values de cession
            '''
            fragf = self.f5hn + self.f5in + self.f5jn
            aragf = self.f5hb + self.f5ib + self.f5jb
            nragf = self.f5hh + self.f5ih + self.f5jh
            mbicf = self.f5kn + self.f5ln + self.f5mn
            abicf = self.f5kb + self.f5lb + self.f5mb
            nbicf = self.f5kh + self.f5lh + self.f5mh 
            maccf = self.f5nn + self.f5on + self.f5pn
            aaccf = self.f5nb + self.f5ob + self.f5pb
            naccf = self.f5nh + self.f5oh + self.f5ph
            mbncf = self.f5hp + self.f5ip + self.f5jp
            abncf = self.f5qb + self.f5rb + self.f5sb
            nbncf = self.f5qh + self.f5rh + self.f5sh
            
            return (fragf + aragf + nragf + mbicf + abicf + 
                    nbicf + maccf + aaccf + naccf + mbncf + 
                    abncf + nbncf )
            # TODO: Prendre en compte les déficits?
#            return fragf_exon + aragf_exon + nragf_exon + mbicf_exon + maxi(abicf_exon-abicf_defe,0) + maxi(nbicf_exon-nbicf_defe,0) + maccf_exon + aaccf_exon + naccf_exon + mbncf_exon + abncf_exon + nbncf_exon 


        # plus values de cession
        self.rpns_pvce = Pvce(self)
        # revenus exonérés
        self.rpns_exo =  Exon(self)

        ## A revenus agricoles 
        table.openWriteMode()
        
        #regime du forfait
        fragf_impo = self.f5ho + self.f5io + self.f5jo
        fragf_pvct = self.f5hw + self.f5iw + self.f5jw
        fragf_timp = fragf_impo + fragf_pvct  # majoration de 25% mais les pvct ne sont pas majorées de 25%
        
        #Régime du bénéfice réel ou transitoire bénéficiant de l'abattement CGA
        aragf_impg = self.f5hc + self.f5ic + self.f5jc
        aragf_defi = self.f5hf + self.f5if + self.f5jf
        aragf_timp = aragf_impg                  # + aragf_impx/5 pas de majoration;
        
        #Régime du bénéfice réel ou transitoire ne bénéficiant pas de l'abattement CGA
        nragf_impg = self.f5hi + self.f5ii + self.f5ji
        nragf_defi = self.f5hl + self.f5il + self.f5jl
        nragf_timp = nragf_impg # + nragf_impx/5 ; # majoration de 25% mais les pvct ne sont pas majorées de 25%
        
        #Jeunes agriculteurs montant de l'abattement de 50% ou 100% ;
        nragf_ajag = self.f5hm + self.f5im + self.f5jm 
        # TODO: à integrer qqpart
        
        # déficits agricole des années antérieurs (imputables uniquement
        # sur des revenus agricoles)
        ragf_timp = fragf_timp + aragf_timp + nragf_timp 
        cond = (self.AUTRE <= P.def_agri_seuil)
        def_agri = cond*(aragf_defi + nragf_defi) + lnot(cond)*mini(ragf_timp, aragf_defi + nragf_defi)
        # TODO : check 2006 cf art 156 du CGI pour 2006
        # sur base 2003:
        # cf menage 3020938 pour le déficit agricole qui peut déduire et ménage
        # 3001872 qui ne peut pas déduire.
        def_agri_ant    = mini(maxi(0,ragf_timp - def_agri), self.f5sq)
        
        ragv = self.f5hn + self.f5ho + self.f5hb + self.f5hc - self.f5hf + self.f5hh + self.f5hi - self.f5hl + self.f5hm
        ragc = self.f5in + self.f5io + self.f5ib + self.f5ic - self.f5if + self.f5ih + self.f5ii - self.f5il + self.f5im
        ragp = self.f5jn + self.f5jo + self.f5jb + self.f5jc - self.f5jf + self.f5jh + self.f5ji - self.f5jl + self.f5jm
        
        table.setFoyer('vous','rag', ragv)
        table.setFoyer('conj','rag', ragc)
        table.setFoyer('pac1','rag', ragp)
        
        self.zragf = ragv + ragc + ragp
        
        ## B revenus industriels et commerciaux professionnels 
        
        #regime micro entreprise
        mbicf_impv = abatv(self.f5ko,P) + abatv(self.f5lo,P) + abatv(self.f5mo,P)
        mbicf_imps = abats(self.f5kp,P) + abats(self.f5lp,P) + abats(self.f5mp,P)
        mbicf_pvct = self.f5kx + self.f5lx + self.f5mx
        mbicf_mvlt = self.f5kr + self.f5lr + self.f5mr
        mbicf_mvct = self.f5hu
        mbicf_timp = mbicf_impv + mbicf_imps - mbicf_mvlt
        
        #Régime du bénéfice réel bénéficiant de l'abattement CGA
        abicf_impn = self.f5kc + self.f5lc + self.f5mc
        abicf_imps = self.f5kd + self.f5ld + self.f5md
        abicf_defn = self.f5kf + self.f5lf + self.f5mf
        abicf_defs = self.f5kg + self.f5lg + self.f5mg
        abicf_timp = abicf_impn + abicf_imps - (abicf_defn + abicf_defs)
        abicf_defe = -mini(abicf_timp,0) 
        # base 2003: cf ménage 3021218 pour l'imputation illimitée de ces déficits.
        
        #Régime du bénéfice réel ne bénéficiant pas de l'abattement CGA
        nbicf_impn = self.f5ki + self.f5li + self.f5mi
        nbicf_imps = self.f5kj + self.f5lj + self.f5mj
        nbicf_defn = self.f5kl + self.f5ll + self.f5ml
        nbicf_defs = self.f5km + self.f5lm + self.f5mm
        nbicf_timp = (nbicf_impn + nbicf_imps) - (nbicf_defn + nbicf_defs)
        nbicf_defe = -mini(nbicf_timp,0) ;
        # base 2003 cf ménage 3015286 pour l'imputation illimitée de ces déficits.
        
        #Abatemment artisant pécheur
        nbicf_apch = self.f5ks + self.f5ls + self.f5ms # TODO : à intégrer qqpart
        
        zbicv = self.f5kn + self.f5ko + self.f5kp + self.f5kb + self.f5kh + self.f5kc + self.f5ki + self.f5kd + self.f5kj - self.f5kf - self.f5kl - self.f5kg - self.f5km + self.f5ks
        zbicc = self.f5ln + self.f5lo + self.f5lp + self.f5lb + self.f5lh + self.f5lc + self.f5li + self.f5ld + self.f5lj - self.f5lf - self.f5ll - self.f5lg - self.f5lm + self.f5ls     
        zbicp = self.f5mn + self.f5mo + self.f5mp + self.f5mb + self.f5mh + self.f5mc + self.f5mi + self.f5md + self.f5mj - self.f5mf - self.f5ml - self.f5mg - self.f5mm + self.f5ms
        
        condv = (self.f5ko>0) & (self.f5kp==0)
        condc = (self.f5lo>0) & (self.f5lp==0)
        condp = (self.f5mo>0) & (self.f5mp==0)
        tauxv = P.microentreprise.vente_taux*condv + P.microentreprise.servi_taux*lnot(condv)
        tauxc = P.microentreprise.vente_taux*condc + P.microentreprise.servi_taux*lnot(condc)
        tauxp = P.microentreprise.vente_taux*condp + P.microentreprise.servi_taux*lnot(condp)
        
        P.cbicf_min = 305
        
        cbicv = mini(self.f5ko+self.f5kp+self.f5kn, maxi(P.cbicf_min,round(self.f5ko*P.microentreprise.vente_taux + self.f5kp*P.microentreprise.servi_taux + self.f5kn*tauxv)))
        cbicc = mini(self.f5lo+self.f5lp+self.f5ln, maxi(P.cbicf_min,round(self.f5lo*P.microentreprise.vente_taux + self.f5lp*P.microentreprise.servi_taux + self.f5ln*tauxc)));
        cbicp = mini(self.f5mo+self.f5mp+self.f5mn, maxi(P.cbicf_min,round(self.f5mo*P.microentreprise.vente_taux + self.f5mp*P.microentreprise.servi_taux + self.f5mn*tauxp)));
        
        ricv = zbicv - cbicv
        ricc = zbicc - cbicc
        ricp = zbicp - cbicp
        
        table.setFoyer('vous','ric', ricv)
        table.setFoyer('conj','ric', ricc)
        table.setFoyer('pac1','ric', ricp)
        
        self.zricf = ricv + ricc + ricp
        
        ## C revenus industriels et commerciaux non professionnels 
        # (revenus accesoires du foyers en nomenclature INSEE)
        #regime micro entreprise
        maccf_impv = abatv(self.f5no,P) + abatv(self.f5oo,P) + abatv(self.f5po,P);
        maccf_imps = abats(self.f5np,P) + abats(self.f5op,P) + abats(self.f5pp,P);
        maccf_pvct = self.f5nx + self.f5ox + self.f5px
        maccf_mvlt = self.f5nr + self.f5or + self.f5pr
        maccf_mvct = self.f5iu
        maccf_timp = maccf_impv + maccf_imps - maccf_mvlt
        
        #Régime du bénéfice réel bénéficiant de l'abattement CGA
        aaccf_impn = self.f5nc + self.f5oc + self.f5pc
        aaccf_imps = self.f5nd + self.f5od + self.f5pd
        aaccf_defn = self.f5nf + self.f5of + self.f5pf
        aaccf_defs = self.f5ng + self.f5og + self.f5pg
        aaccf_timp = maxi(0,aaccf_impn + aaccf_imps - (aaccf_defn + aaccf_defs))
        
        #Régime du bénéfice réel ne bénéficiant pas de l'abattement CGA
        naccf_impn = self.f5ni + self.f5oi + self.f5pi
        naccf_imps = self.f5nj + self.f5oj + self.f5pj
        naccf_defn = self.f5nl + self.f5ol + self.f5pl
        naccf_defs = self.f5nm + self.f5om + self.f5pm
        naccf_timp = maxi(0,naccf_impn + naccf_imps - (naccf_defn + naccf_defs))
        # TODO : base 2003 comprendre pourquoi le ménage 3018590 n'est pas imposé sur 5nj.
        
        ## E revenus non commerciaux non professionnels 
        #regime déclaratif special ou micro-bnc
        mncnp_impo = abatnc(self.f5ku,P) + abatnc(self.f5lu,P) + abatnc(self.f5mu,P);
        mncnp_pvct = self.f5ky + self.f5ly + self.f5my
        mncnp_mvlt = self.f5kw + self.f5lw + self.f5mw
        mncnp_mvct = self.f5ju;
        mncnp_timp = mncnp_impo - mncnp_mvlt;
        
        # TODO : 2006 
        # régime de la déclaration controlée 
        cncnp_bene = self.f5sn + self.f5ns + self.f5os
        cncnp_defi = self.f5sp + self.f5nu + self.f5ou + self.f5sr
        #total 11
        cncnp_timp = maxi(0,cncnp_bene - cncnp_defi); 
        # TODO : abatement jeunes créateurs 
        
        zaccv = self.f5nn + self.f5no + self.f5np + self.f5nb + self.f5nc + self.f5nd - self.f5nf - self.f5ng + self.f5nh + self.f5ni + self.f5nj - self.f5nl - self.f5nm + self.f5ku + self.f5sn - self.f5sp + self.f5sv ;
    
        zaccc = self.f5on + self.f5oo + self.f5op + self.f5ob + self.f5oc + self.f5od - self.f5of - self.f5og + self.f5oh + self.f5oi + self.f5oj - self.f5ol - self.f5om + self.f5lu + self.f5ns - self.f5nu + self.f5sw ;
        
        zaccp = self.f5pn + self.f5po + self.f5pp + self.f5pb + self.f5pc + self.f5pd - self.f5pf - self.f5pg + self.f5ph + self.f5pi + self.f5pj - self.f5pl - self.f5pm + self.f5mu + self.f5os - self.f5ou + self.f5sx ;
        
        condv = (self.f5no >0) & (self.f5np ==0) ;
        condc = (self.f5oo >0) & (self.f5op ==0) ;
        condp = (self.f5po >0) & (self.f5pp ==0) ;
        tauxv = P.microentreprise.vente_taux*condv + P.microentreprise.servi_taux*lnot(condv) ;
        tauxc = P.microentreprise.vente_taux*condc + P.microentreprise.servi_taux*lnot(condc) ;
        tauxp = P.microentreprise.vente_taux*condp + P.microentreprise.servi_taux*lnot(condp) ;
        
        caccv = mini(self.f5no + self.f5np + self.f5nn + self.f5ku, maxi(P.nc_abat_min, 
                round(self.f5no*P.microentreprise.vente_taux + self.f5np*P.microentreprise.servi_taux 
                + self.f5nn*tauxv + self.f5ku*P.nc_abat_taux )));
        caccc = mini(self.f5oo + self.f5op + self.f5on + self.f5lu, maxi(P.nc_abat_min, 
                round(self.f5oo*P.microentreprise.vente_taux + self.f5op*P.microentreprise.servi_taux 
                + self.f5on*tauxc + self.f5lu*P.nc_abat_taux )));
        caccp = mini(self.f5po + self.f5pp + self.f5pn + self.f5mu, maxi(P.nc_abat_min, 
                round(self.f5po*P.microentreprise.vente_taux + self.f5pp*P.microentreprise.servi_taux 
                + self.f5pn*tauxp + self.f5mu*P.nc_abat_taux )));
        
        racv = zaccv - caccv
        racc = zaccc - caccc
        racp = zaccp - caccp

        table.setFoyer('vous', 'rac', racv)
        table.setFoyer('conj', 'rac', racc)
        table.setFoyer('pac1', 'rac', racp)
        
        
        self.zracf = racv + racc + racp
        
        ## D revenus non commerciaux professionnels
        
        #regime déclaratif special ou micro-bnc
        mbncf_impo = abatnc(self.f5hq,P) + abatnc(self.f5iq,P) + abatnc(self.f5jq,P)
        mbncf_pvct = self.f5hv + self.f5iv + self.f5jv
        mbncf_mvlt = self.f5hs + self.f5is + self.f5js
        mbncf_mvct = self.f5kz
        mbncf_timp = mbncf_impo - mbncf_mvlt
        
        #regime de la déclaration contrôlée bénéficiant de l'abattement association agréée
        abncf_impo = self.f5qc + self.f5rc + self.f5sc
        abncf_defi = self.f5qe + self.f5re + self.f5se
        abncf_timp = abncf_impo - abncf_defi;
        
        #regime de la déclaration contrôlée ne bénéficiant pas de l'abattement association agréée
        nbncf_impo = self.f5qi + self.f5ri + self.f5si ;
        nbncf_defi = self.f5qk + self.f5rk + self.f5sk ;
        nbncf_timp = nbncf_impo - nbncf_defi;
        # cf base 2003 menage 3021505 pour les deficits
        
        zbncv = self.f5hp + self.f5hq + self.f5qb + self.f5qh + self.f5qc + self.f5qi - self.f5qe - self.f5qk + self.f5ql + self.f5qm;
        zbncc = self.f5ip + self.f5iq + self.f5rb + self.f5rh + self.f5rc + self.f5ri - self.f5re - self.f5rk + self.f5rl + self.f5rm;
        zbncp = self.f5jp + self.f5jq + self.f5sb + self.f5sh + self.f5sc + self.f5si - self.f5se - self.f5sk + self.f5sl ;
        
        cbncv = mini(self.f5hp + self.f5hq, maxi(P.nc_abat_min, round((self.f5hp + self.f5hq)*P.nc_abat_taux)))
        cbncc = mini(self.f5ip + self.f5iq, maxi(P.nc_abat_min, round((self.f5ip + self.f5iq)*P.nc_abat_taux)))
        cbncp = mini(self.f5jp + self.f5jq, maxi(P.nc_abat_min, round((self.f5jp + self.f5jq)*P.nc_abat_taux)))
        
        rncv = zbncv - cbncv
        rncc = zbncc - cbncc
        rncp = zbncp - cbncp

        table.setFoyer('vous','rnc', rncv)
        table.setFoyer('conj','rnc', rncc)
        table.setFoyer('pac1','rnc', rncp)
                
        self.zrncf =  rncv +  rncv +  rncp
        
        ## Totaux
        atimp = aragf_timp + abicf_timp +  aaccf_timp + abncf_timp;
        ntimp = nragf_timp + nbicf_timp +  naccf_timp + nbncf_timp;
        
        majo_cga = maxi(0,P.cga_taux2*(ntimp+fragf_impo)); # pour ne pas avoir à
                                                # majorer les déficits
        #total 6
        rev_NS = fragf_impo + fragf_pvct + atimp + ntimp + majo_cga - def_agri - def_agri_ant 
        
        #revenu net après abatement
        # total 7
        rev_NS_mi = mbicf_timp + maccf_timp + mbncf_timp + mncnp_timp 
        
        
        #plus value ou moins value à court terme
        #activité exercée à titre professionnel 
        # total 8
        pvct_pro = mbicf_pvct - mbicf_mvct + mbncf_pvct - mbncf_mvct
        #activité exercée à titre non professionnel
        #revenus industriels et commerciaux non professionnels 
        # total 9
        pvct_icnpro = mini(maccf_pvct - maccf_mvct, maccf_timp) 
        #revenus non commerciaux non professionnels 
        # total 10
        pvct_ncnpro = mini(mncnp_pvct - mncnp_mvct, mncnp_timp)
        
        #total 11 cncnp_timp déja calculé        
        
        self.rpns_pvct = fragf_pvct + mbicf_pvct + maccf_pvct + mbncf_pvct + mncnp_pvct;
        self.rpns_mvct = mbicf_mvct + maccf_mvct + mbncf_mvct + mncnp_mvct;
        self.rpns_mvlt = mbicf_mvlt + maccf_mvlt + mbncf_mvlt + mncnp_mvlt;
        
        # imp_plusval_ces = plusval_ces*plusvalces_taux;
        RPNS = rev_NS + rev_NS_mi + pvct_pro + pvct_icnpro + pvct_ncnpro + cncnp_timp
        
        # Calcul des revenus individuels
        self.rpnsv = ragv + ricv + racv + rncv
        self.rpnsc = ragc + ricc + racc + rncc
        self.rpnsp = ragp + ricp + racp + rncp
        
        table.setFoyer('vous', 'rpns', self.rpnsv)
        table.setFoyer('conj', 'rpns', self.rpnsc)
        table.setFoyer('pac1', 'rpns', self.rpnsp)        
        
        table.close_()

        return RPNS

    def RevCat(self,P):
        '''
        Revenus Categoriels
        '''
        table = self.population
        TSPR = self.Tspr(P.tspr, table)
        RVCM = self.Rvcm(P.rvcm, table)
        RFON = self.Rfon(P, table)
        self.AUTRE = TSPR + RVCM + RFON
        RPNS = self.Rpns(P.rpns, table)
        return TSPR, RVCM, RFON, RPNS

    def Deficit_anterieur(self):
        table = self.population
        table.openReadMode()
        FA = table.getFoyer('vous', 'f6fa', 'foyer')
        FB = table.getFoyer('vous', 'f6fb', 'foyer')
        FC = table.getFoyer('vous', 'f6fc', 'foyer')
        FD = table.getFoyer('vous', 'f6fd', 'foyer')
        FE = table.getFoyer('vous', 'f6fe', 'foyer')
        FL = table.getFoyer('vous', 'f6fl', 'foyer')
        table.close_()
        return FA + FB + FC + FD + FE + FL


    def Charges_deductibles(self, P):
        '''
        Charges déductibles
        '''
        table = self.population

        table.openReadMode()
        niches1, niches2, ind_rfr = charges_deductibles.niches(self.year)
        charges_deductibles.charges_calc(self, P, table, niches1, niches2, ind_rfr)

        ## stockage des pensions dans les individus
        self.zalvf = charges_deductibles.penali(self, P, table)
        table.close_()

        table.openWriteMode()
        table.setColl('alv', -self.zalvf)
        table.close_()

    def Abattements(self, P, rng):
        '''
        Abattements spéciaux 
        - pour personnes âges ou invalides : Si vous êtes âgé(e) de plus de 65 ans
          ou invalide (titulaire d’une pension d’invalidité militaire ou d’accident 
          du travail d’au moins 40 % ou titulaire de la carte d’invalidité), vous 
          bénéficiez d’un abattement de 2 172 € si le revenu net global de votre 
          foyer fiscal n’excède pas 13 370 € ; il est de 1 086 € si ce revenu est 
          compris entre 13 370 € et 21 570 €. Cet abattement est doublé si votre 
          conjoint ou votre partenaire de PACS remplit également ces conditions 
          d’âge ou d’invalidité. Cet abattement sera déduit automatiquement lors 
          du calcul de l’impôt.
        - pour enfants à charge ayant fondé un foyer distinct : Si vous avez accepté
          le rattachement de vos enfants mariés ou pacsés ou de vos enfants 
          célibataires, veufs, divorcés, séparés, chargés de famille, vous bénéficiez 
          d’un abattement sur le revenu imposable de 5 495 € par personne ainsi 
          rattachée. Si l’enfant de la personne rattachée est réputé à charge de 
          l’un et l’autre de ses parents (garde alternée), cet abattement est divisé 
          par deux soit 2 748€. Exemple : 10 990 € pour un jeune ménage et 8 243 €
          pour un célibataire avec un jeune enfant en résidence alternée.
        '''
        as_inv = ((rng <= P.inv_max1) + ((rng > P.inv_max1)&( rng <= P.inv_max2))*0.5)*(((self.agev>=65)| self.caseP)*1 + 1*(((self.agec>=65)| self.caseF)&(self.agec>0)))*P.inv_montant ;        
        as_enf = self.nbN*P.enf_montant; #TODO Comment prendre en compte les enfants majeurs en garde alternée?
        return mini(rng, as_inv + as_enf)

    def Non_imposabilite(self, rni, nbptr, P):
        '''
        Renvoie 1 si le foyer est imposable, 0 sinon
        '''
        seuil = P.seuil + (nbptr - 1)*P.supp
        return rni >= seuil


    def Nbpt(self,P):
        '''
        nombre de parts du foyer
        note 1 enfants et résidence alternée (formulaire 2041 GV page 10)
        
        P.enf1 : nb part 2 premiers enfants
        P.enf2 : nb part enfants de rang 3 ou plus
        P.inv1 : nb part supp enfants invalides (I, G)
        P.inv2 : nb part supp adultes invalides (R)
        P.not31 : nb part supp note 3 : cases W ou G pour veuf, celib ou div
        P.not32 : nb part supp note 3 : personne seule ayant élevé des enfants
        P.not41 : nb part supp adultes invalides (vous et/ou conjoint) note 4
        P.not42 : nb part supp adultes anciens combattants (vous et/ou conjoint) note 4
        P.not6 : nb part supp note 6
        P.isol : demi-part parent isolé (T)
        P.edcd : enfant issu du mariage avec conjoint décédé;
        '''
        noPAC  = self.nbPAC == 0 # Aucune personne à charge en garde exclusive
        hasPAC = lnot(noPAC)
        noAlt  = self.nbH == 0 # Aucun enfant à charge en garde alternée
        hasAlt = lnot(noAlt)
        
        ## nombre de parts liées aux enfants à charge
        # que des enfants en résidence alternée
        enf1 = (noPAC & hasAlt)*(P.enf1*mini(self.nbH,2)*0.5 + P.enf2*maxi(self.nbH-2,0)*0.5)
        # pas que des enfants en résidence alternée
        enf2 = (hasPAC & hasAlt)*((self.nbPAC==1)*(P.enf1*mini(self.nbH,1)*0.5 + P.enf2*maxi(self.nbH-1,0)*0.5) + (self.nbPAC>1)*(P.enf2*self.nbH*0.5))
        # pas d'enfant en résidence alternée    
        enf3 = P.enf1*mini(self.nbPAC,2) + P.enf2*maxi((self.nbPAC-2),0)
        
        enf = enf1 + enf2 + enf3 
        ## note 2 : nombre de parts liées aux invalides (enfant + adulte)
        n2 = P.inv1*(self.nbG + self.nbI/2) + P.inv2*self.nbR 
        
        ## note 3 : Pas de personne à charge
        # - invalide ;
        n31a = P.not31a*( noPAC & noAlt & self.caseP )
        # - ancien combatant ;
        n31b = P.not31b*( noPAC & noAlt & ( self.caseW | self.caseG ) ) 
        n31 = maxi(n31a,n31b)
        # - personne seule ayant élevé des enfants
        n32 = P.not32*( noPAC & noAlt &(( self.caseE | self.caseK) & lnot(self.caseN)))
        n3 = maxi(n31,n32)
        ## note 4 Invalidité de la personne ou du conjoint pour les mariés ou
        ## jeunes veuf(ve)s
        n4 = maxi(P.not41*(1*self.caseP + 1*self.caseF), P.not42*(self.caseW | self.caseS))
        
        ## note 5
        #  - enfant du conjoint décédé
        n51 =  P.cdcd*(self.caseL & ((self.nbF + self.nbJ)>0))
        #  - enfant autre et parent isolé
        n52 =  P.isol*self.caseT*( ((noPAC & hasAlt)*((self.nbH==1)*0.5 + (self.nbH>=2))) + 1*hasPAC)
        n5 = maxi(n51,n52)
        
        ## note 6 invalide avec personne à charge
        n6 = P.not6*(self.caseP & (hasPAC | hasAlt))
        
        ## note 7 Parent isolé
        n7 = P.isol*self.caseT*((noPAC & hasAlt)*((self.nbH==1)*0.5 + (self.nbH>=2)) + 1*hasPAC)
        
        ## Régime des mariés ou pacsés
        m = 2 + enf + n2 + n4
        
        ## veufs  hors self.jveuf
        v = 1 + enf + n2 + n3 + n5 + n6
        
        ## celib div
        c = 1 + enf + n2 + n3 + n6 + n7
        
        return (self.marpac | self.jveuf)*m + (self.veuf & lnot(self.jveuf))*v + self.celdiv*c
        
    def PlafQf(self,P):
        '''
        Plafonnement du quotient familial
        '''
        I = self.IR_brut
        A = BarmMar(self.revimp/self.nbadult,P.bareme)
        A = self.nbadult*A    
    
        aa0 = (self.nbptr-self.nbadult)*2           #nombre de demi part excédant self.nbadult
        # on dirait que les impôts font une erreur sur aa1 (je suis obligé de
        # diviser par 2)
        aa1 = mini((self.nbptr-1)*2,2)/2  # deux première demi part excédants une part
        aa2 = maxi((self.nbptr-2)*2,0)    # nombre de demi part restantes
        # self.celdiv parents isolés
        condition61 = (self.celdiv==1) & self.caseT
        B1 = P.plafond_qf.celib_enf*aa1 + P.plafond_qf.marpac*aa2
        # tous les autres
        B2 = P.plafond_qf.marpac*aa0                 #si autre
        # self.celdiv, veufs (non self.jveuf) vivants seuls et autres conditions TODO année codéee en dur
        condition63 = ((self.celdiv==1) | ((self.veuf==1) & lnot(self.jveuf))) & lnot(self.caseN) & (self.nbPAC==0) & (self.caseK | self.caseE) & (self.caseH<1981)
        B3 = P.plafond_qf.celib
    
        B = B1*condition61 + \
            B2*(lnot(condition61 | condition63)) + \
            B3*(condition63 & lnot(condition61))
        C = maxi(0,A-B);
        # Impôt après plafonnement
        IP0 = I*(I>=C) + C*(I<C);
    
        # 6.2 réduction d'impôt pratiquée sur l'impot après plafonnement et le cas particulier des DOM
    
        # pas de réduction complémentaire
        condition62a = (I>=C);
        # réduction complémentaire
        condition62b = (I<C);
        # self.celdiv self.veuf
        condition62caa0 = (self.celdiv | (self.veuf & lnot(self.jveuf)))
        condition62caa1 = (self.nbPAC==0)&(self.caseP | self.caseG | self.caseF | self.caseW)
        condition62caa2 = self.caseP & ((self.nbF-self.nbG>0)|(self.nbH - self.nbI>0))
        condition62caa3 = lnot(self.caseN) & (self.caseE | self.caseK )  & (self.caseH>=1981)
        condition62caa  = condition62caa0 & (condition62caa1 | condition62caa2 | condition62caa3)
        # marié pacs
        condition62cab = (self.marpac | self.jveuf) & self.caseS & lnot(self.caseP | self.caseF)
        condition62ca =    (condition62caa | condition62cab);
    
        # plus de 590 euros si on a des plus de
        condition62cb = ((self.nbG+self.nbR+self.nbI)>0) | self.caseP | self.caseF
        D = P.plafond_qf.reduc_postplafond*(condition62ca + ~condition62ca*condition62cb*( 1*self.caseP + 1*self.caseF + self.nbG + self.nbR + self.nbI/2 ))
    
        E = maxi(0,A-I-B)
        Fo = D*(D<=E) + E*(E<D)
        IP1=IP0-Fo;
    
        # TODO :6.3 Cas particulier: Contribuables domiciliés dans les DOM.    
        # conditionGuadMarReu =
        # conditionGuyane=
        # conitionDOM = conditionGuadMarReu | conditionGuyane;
        # postplafGuadMarReu = 5100;
        # postplafGuyane = 6700;
        # IP2 = IP1 - conditionGuadMarReu*min( postplafGuadMarReu,.3*IP1)  - conditionGuyane*min(postplafGuyane,.4*IP1);
    
    
        # Récapitulatif
        return condition62a*IP0 + condition62b*IP1 # IP2 si DOM

    def Decote(self, IP, P):
        return (IP < P.seuil)*(P.seuil - IP)*0.5

    def Reductions(self, IPnet, P, table):
        ''' 
        Réductions d'impôts
        '''
        table.openReadMode()
        niches = reductions_impots.niches(self.year)
        reducs = zeros(self.taille)
        for niche in niches:
            reducs += niche(self, P, table)
             
        table.close_()
        return mini(reducs, IPnet)
    
    def Plus_values(self, P, table):
        table.openReadMode()
        VG = table.getFoyer('vous', 'f3vg', 'foyer')
        VH = table.getFoyer('vous', 'f3vh', 'foyer')
        VL = table.getFoyer('vous', 'f3vl', 'foyer')
        VM = table.getFoyer('vous', 'f3vm', 'foyer')
        VI = table.getFoyer('vous', 'f3vi', 'foyer')
        VF = table.getFoyer('vous', 'f3vf', 'foyer')
        if self.year >= 2008:
            VD = table.getFoyer('vous', 'f3vd', 'foyer')
        table.close_()
        if self.year <= 2007:
            # revenus taxés à un taux proportionnel
            self.rdp = maxi(0,VG - VH) + VL + self.rpns_pvce + VM + VI + VF

            return round(P.pvce*self.rpns_pvce + 
                         P.taux1*maxi(0,VG - VH) + 
                         P.caprisque*VL + 
                         P.pea*VM +
                         P.taux3*VI +
                         P.taux4*VF )
        elif self.year >= 2008:
            # revenus taxés à un taux proportionnel
            self.rdp = maxi(0,VG - VH) + VD + VL + self.rpns_pvce + VM + VI + VF
            return round(P.pvce*self.rpns_pvce + 
                         P.taux1*(maxi(0,VG - VH) + VD) +
                         P.caprisque*VL + 
                         P.pea*VM +
                         P.taux3*VI +
                         P.taux4*VF )

    def Credits(self, P, table):
        '''
        Imputations (crédits d'impôts)
        '''
        table.openReadMode()
        niches = credits_impots.niches(self.year)
        reducs = zeros(self.taille)
        for niche in niches:
            reducs += niche(self, P, table)
        table.close_()

        ppe = self.Ppe(P.ppe)

        return reducs + ppe
        
    def Ppe(self,P):
        '''
        Prime pour l'emploi
        '''
        table = self.population
        table.openReadMode()
        AJ, BJ, CJ, DJ, EJ = table.getFoyer(self.people, 'sal')
        AX, BX, CX, DX, QX = table.getFoyer(self.people, 'ppeCheckBox')
        AV, BV, CV, DV, QV = table.getFoyer(self.people, 'ppeHeure')
        AU, BU, CU, DU, EU = table.getFoyer(self.people, 'hsup')
        TV = table.getFoyer('vous', 'f1tv', 'foyer') 
        UV = table.getFoyer('vous', 'f1uv', 'foyer') 
        TW = table.getFoyer('vous', 'f1tw', 'foyer') 
        UW = table.getFoyer('vous', 'f1uw', 'foyer') 
        TX = table.getFoyer('vous', 'f1tx', 'foyer') 
        UX = table.getFoyer('vous', 'f1ux', 'foyer') 
        AQ = table.getFoyer('vous', 'f1aq', 'foyer') 
        BQ = table.getFoyer('vous', 'f1bq', 'foyer') 
        LZ = table.getFoyer('vous', 'f1lz', 'foyer') 
        MZ = table.getFoyer('vous', 'f1mz', 'foyer') 
        VJ = table.getFoyer('vous', 'f3vj', 'foyer')
        VK = table.getFoyer('vous', 'f3vk', 'foyer') 
        NV = table.getFoyer('vous', 'f5nv', 'foyer') 
        OV = table.getFoyer('vous', 'f5ov', 'foyer') 
        PV = table.getFoyer('vous', 'f5pv', 'foyer') 
        NW = table.getFoyer('vous', 'f5nw', 'foyer') 
        OW = table.getFoyer('vous', 'f5ow', 'foyer') 
        PW = table.getFoyer('vous', 'f5pw', 'foyer') 
        table.close_()

        # coefficient de conversion en cas de changement de situation en cours
        # d'année
        nbJour = (self.jourXYZ==0) + self.jourXYZ;
        coef_conv = 360/nbJour
        
        # Conditions d'éligibilité
        eligib = (self.rfr*coef_conv) <= (\
            ((self.veuf==1)|(self.celdiv==1))*(P.eligi1 + 2*maxi(self.nbptr-1,0)*P.eligi3) \
            + self.marpac*(P.eligi2 + 2*maxi(self.nbptr-2,0)*P.eligi3))

        # Revenu d'Activité Salariée (RAS)
        RASv = AJ + AU + TV + TW + TX + AQ + LZ + VJ
        RASc = BJ + BU + UV + UW + UX + BQ + MZ + VK
        RAS1 = CJ + CU
        RAS2 = DJ + DU
        RAS3 = EJ + EU
        
        # Revenu d'Activité Non Salariée (RANS)
        RANSv = mini(0,self.rpnsv)/P.abatns + maxi(0,self.rpnsv)*P.abatns;
        RANSc = mini(0,self.rpnsc)/P.abatns + maxi(0,self.rpnsc)*P.abatns;
        RANS1 = mini(0,self.rpnsp)/P.abatns + maxi(0,self.rpnsp)*P.abatns;
        
        # Base
        basevi = RASv + RANSv;
        baseci = RASc + RANSc;
        base1i = RAS1 + RANS1; # Pb: même enfant à charge cumule les 2 activités?
        base2i = RAS2 ; # Pb: même enfant à charge cumule les 2 activités?
        base3i = RAS3 ; # Pb: même enfant à charge cumule les 2 activités?
        
        
        # TODO : regarder comment sont pris en compte les 6 qui ont remplit les
        # av et ax.
        fracv_sa = AV/P.TP_nbh
        fracv_ns = NV/P.TP_nbj
        fracc_sa = BV/P.TP_nbh
        fracc_ns = OV/P.TP_nbj
        frac1_sa = CV/P.TP_nbh
        frac1_ns = PV/P.TP_nbj
        frac2_sa = DV/P.TP_nbh
        frac3_sa = QV/P.TP_nbh
        
        TPv = (AX == 1)|(NW == 1)|(fracv_sa + fracv_ns >= 1) |((fracv_ns == 0)&(RANSv   > 0));# > RASv));
        TPc = (BX == 1)|(OW == 1)|(fracc_sa + fracc_ns >= 1) |((fracc_ns == 0)&(RANSc   > 0));# > RASc));
        TP1 = (CX == 1)|(PW == 1)|(frac1_sa + frac1_ns >= 1) |((frac1_ns == 0)&(RANS1   > 0));# > RAS1));
        TP2 = (DX == 1)|(frac2_sa >= 1);
        TP3 = (QX == 1)|(frac3_sa >= 1);
                
        coeff_TPv = TPv + ~TPv*(fracv_sa + fracv_ns) ;
        coeff_TPc = TPc + ~TPc*(fracc_sa + fracc_ns);
        coeff_TP1 = TP1 + ~TP1*(frac1_sa + frac1_ns);
        coeff_TP2 = TP2 + ~TP2*frac2_sa ;
        coeff_TP3 = TP3 + ~TP3*frac3_sa;
        
        basev = basevi/(coeff_TPv + (coeff_TPv==0))*coef_conv;
        basec = baseci/(coeff_TPc + (coeff_TPc==0))*coef_conv;
        base1 = base1i/(coeff_TP1 + (coeff_TP1==0))*coef_conv;
        base2 = base2i/(coeff_TP2 + (coeff_TP2==0))*coef_conv;
        base3 = base3i/(coeff_TP3 + (coeff_TP3==0))*coef_conv;
                
        eliv = (basevi >= P.seuil1)&(coeff_TPv!=0);
        elic = (baseci >= P.seuil1)&(coeff_TPc!=0);
        eli1 = (base1i >= P.seuil1)&(coeff_TP1!=0);
        eli2 = (base2i >= P.seuil1)&(coeff_TP2!=0);
        eli3 = (base3i >= P.seuil1)&(coeff_TP3!=0);
        
        nbPAC_ppe = maxi(0,self.nbPAC - eli1 - eli2 -eli3  );
        
        #condition sur Revenu fiscal de référence
        
        ligne2 = self.marpac & lxor(basevi >= P.seuil1,baseci >= P.seuil1);
        ligne3 = (self.celdiv | self.veuf) & self.caseT & lnot(self.veuf & self.caseT & self.caseL)
        ligne1 = lnot(ligne2) & lnot(ligne3)
        
        base_monact = ligne2*(eliv*basev + elic*basec);
        base_monacti = ligne2*(eliv*basevi + elic*baseci);
        
        # calcul des primes individuelles.
        ppev = eliv/coef_conv*(\
            ((ligne1 |ligne3) & (basev <= P.seuil2))*(basev)*P.taux1 + \
            ((ligne1 |ligne3) & (basev> P.seuil2) & (basev <= P.seuil3))*(P.seuil3 - basev)*P.taux2 + \
            (ligne2 & (basev <= P.seuil2))*(basev*P.taux1 ) +\
            (ligne2 & (basev >  P.seuil2) & (basev <= P.seuil3))*((P.seuil3 - basev)*P.taux2)+ \
            (ligne2 & (basev> P.seuil4) & (basev <= P.seuil5))*(P.seuil5 - basev)*P.taux3);
        
        ppec =  elic/coef_conv*(\
            ((ligne1 |ligne3) & (basec <= P.seuil2))*(basec)*P.taux1 + \
            ((ligne1 |ligne3) & (basec> P.seuil2) & (basec <= P.seuil3))*(P.seuil3 - basec)*P.taux2 + \
            (ligne2 &  (basec <= P.seuil2))*(basec*P.taux1 ) +\
            (ligne2 & (basec> P.seuil2) & (basec <= P.seuil3))*((P.seuil3 - basec)*P.taux2)+ \
            (ligne2 & (basec> P.seuil4) & (basec <= P.seuil5))*(P.seuil5 - basec)*P.taux3);
        
        ppe1 =  eli1/coef_conv*(\
            (base1 <= P.seuil2)*(base1)*P.taux1 + \
            ((base1> P.seuil2) & (base1 <= P.seuil3))*(P.seuil3 - base1)*P.taux2 );
        
        ppe2 =  eli2/coef_conv*(\
            (base2 <= P.seuil2)*(base2)*P.taux1 + \
            ((base2> P.seuil2) & (base2 <= P.seuil3))*(P.seuil3 - base2)*P.taux2 );
        
        ppe3 =  eli3/coef_conv*(\
            (base3 <= P.seuil2)*(base3)*P.taux1 + \
            ((base3> P.seuil2) & (base3 <= P.seuil3))*(P.seuil3 - base3)*P.taux2 );
        
        
        ppe_monact_vous = (eliv & ligne2 & (basevi>=P.seuil1) & (basev <= P.seuil4))*P.monact ;
        ppe_monact_conj = (elic & ligne2 & (baseci>=P.seuil1) & (basec <= P.seuil4))*P.monact ;
        
        maj_pac = eligib*(eliv|elic)*(\
            (ligne1 & self.marpac & ((ppev+ppec)!=0) & (mini(basev,basec)<= P.seuil3))*P.pac*(nbPAC_ppe + self.nbH*0.5) + \
            (ligne1 & (self.celdiv | self.veuf) & eliv & (basev<=P.seuil3))*P.pac*(nbPAC_ppe + self.nbH*0.5) + \
            (ligne2 & (base_monacti >= P.seuil1) & (base_monact <= P.seuil3))*P.pac*(nbPAC_ppe + self.nbH*0.5) + \
            (ligne2 & (base_monact > P.seuil3) & (base_monact <= P.seuil5))*P.pac*((nbPAC_ppe!=0) + 0.5*((nbPAC_ppe==0) & (self.nbH!=0))) + \
            (ligne3 & (basevi >=P.seuil1) & (basev <= P.seuil3))*((mini(nbPAC_ppe,1)*2*P.pac + maxi(nbPAC_ppe-1,0)*P.pac) + (nbPAC_ppe==0)*(mini(self.nbH,2)*P.pac + maxi(self.nbH-2,0)*P.pac*0.5)) + \
            (ligne3 & (basev  > P.seuil3) & (basev <= P.seuil5))*P.pac*((nbPAC_ppe!=0)*2 +((nbPAC_ppe==0) & (self.nbH!=0)))) 
        
        PPE_vous = eligib*(ppev*((coeff_TPv<=0.5)*coeff_TPv*1.45 + (coeff_TPv>0.5)*(0.55*coeff_TPv + 0.45))+ppe_monact_vous)
        PPE_conj = eligib*(ppec*((coeff_TPc<=0.5)*coeff_TPc*1.45 + (coeff_TPc>0.5)*(0.55*coeff_TPc + 0.45))+ppe_monact_conj)
        PPE_pac1 = eligib*ppe1*((coeff_TP1<=0.5)*coeff_TP1*1.45 + (coeff_TP1>0.5)*(0.55*coeff_TP1 + 0.45))
        PPE_pac2 = eligib*ppe2*((coeff_TP2<=0.5)*coeff_TP2*1.45 + (coeff_TP2>0.5)*(0.55*coeff_TP2 + 0.45))
        PPE_pac3 = eligib*ppe3*((coeff_TP3<=0.5)*coeff_TP3*1.45 + (coeff_TP3>0.5)*(0.55*coeff_TP3 + 0.45))
        
        PPE_tot = PPE_vous + PPE_conj + PPE_pac1 + PPE_pac2 + PPE_pac3 +  maj_pac
        
        PPE_tot = (PPE_tot!=0)*maxi(P.versmin,PPE_vous + PPE_conj + PPE_pac1 + PPE_pac2 + PPE_pac3 + maj_pac)
                
        self.mnrbvo = PPE_vous
        self.mnrbcj = PPE_conj
        self.mnrbpc = PPE_pac1 + PPE_pac2 + PPE_pac3
        self.mnrbmf = maj_pac
        self.mnrbtp = PPE_tot
        self.ppetot = PPE_tot
        self.zppef  = PPE_tot
        
        table.openWriteMode()
        table.setColl('ppe',self.zppef)
        table.close_()

        return PPE_tot
        
 
        
        