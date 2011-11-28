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
from tableWriter import CAT
import numpy as np
from numpy import maximum as max_, minimum as min_, logical_not as not_
from Utils import Bareme, BarmMar, Dicts2Object
from parametres.paramData import Tree2Object

salcats = ['cadre', 'noncadre', 'fonc']


class Object(object):
    def __init__(self):
        object.__init__(self)

class cotsoccal(object):
    def __init__(self, population, P, P_defaut):
        self.population= population
        self.year = self.population.year
        self.n = self.population.nbInd
        self.bareme = self.preproc_param(P)        
        self.initialize(self.preproc_param(P_defaut))        
        self.calculate()
                
    def calculate(self):
        
        # Heures supplémentaires exonérées
        if not self.bareme.ir.autre.hsup_exo:
            self.sal += self.hsup
            self.hsup = 0*self.hsup
                        

        crdsact = self.Crds(self.salbrut- self.hsup, self.bareme.crds.act)

        cotsal, cotpat, alleg_fillon = self.CotSocSal(self.salbrut, self.hsup, self.cat)

        sal = self.salbrut + csgactd + cotsal - self.hsup

        # Revenus de remplacement

        csgchod, csgchoi = self.CsgCho(self.chobrut)
        crdscho = self.Crds(self.chobrut, self.bareme.crds.act)
        
        # Exonération de CSG et de CRDS sur les revenus du chômage 
        # et des préretraites si cela abaisse ces revenus sous le smic brut        
        # TODO mettre un trigger pour l'éxonération des revenus du chômage sous un smic
        isnotexo = self.cho > self.cho_seuil_exo                 
        
        table.setIndiv('csgchod', isnotexo*csgchod)
        table.setIndiv('csgchoi', isnotexo*csgchoi)
        table.setIndiv('crdscho', isnotexo*crdscho)

        chobrut = isnotexo*self.chobrut + not_(isnotexo)*self.cho
        table.setIndiv('chobrut', chobrut)
        table.setIndiv('cho', chobrut + isnotexo*csgchod)
        
        csgrstd, csgrsti = self.CsgRst(self.rstbrut)
        table.setIndiv('csgrstd', csgrstd)
        table.setIndiv('csgrsti', csgrsti)
        table.setIndiv('rst', self.rstbrut + csgrstd)

        crdsrst = self.Crds(self.rstbrut, self.bareme.crds.rst)
        table.setIndiv('crdsrst', crdsrst)
        
        # Revenus du capital
        # CSG sur les revenus du patrimoine imposés au barême 
        
        # TODO: CHECK la csg déductible en 2006 est case GH
        # TODO:  la revenus soumis aux csg déductible et imposable sont en CG et BH en 2010 
                 
        csgcap_bar     = - rev_cap_bar*self.bareme.csg.capital.glob
        crdscap_bar    = - rev_cap_bar*self.bareme.crds.capital
        prelsoccap_bar = - rev_cap_bar*self.bareme.prelsoc.total

        verse = (-csgcap_bar - crdscap_bar - prelsoccap_bar) > self.bareme.csg.capital.nonimp
#        verse=1
        # CSG sur les revenus du patrimoine non imposés au barême (contributions sociales déjà prélevées)
        csgcap_lib = - rev_cap_lib*self.bareme.csg.capital.glob        
        crdscap_lib  = - rev_cap_lib*self.bareme.crds.capital
        prelsoccap_lib = - rev_cap_lib*self.bareme.prelsoc.total
                
        table.setIndiv('csgcap_bar', csgcap_bar*verse)
        table.setIndiv('prelsoccap_bar', prelsoccap_bar*verse)
        table.setIndiv('crdscap_bar', crdscap_bar*verse)
        
        table.setIndiv('csgcap_lib', csgcap_lib)
        table.setIndiv('prelsoccap_lib', prelsoccap_lib)
        table.setIndiv('crdscap_lib', crdscap_lib)
        
        # Landais Piketty Saez
        table.close_()
        
        if self.year >= 2010:
            ir_lps = self.impot_LPS(self.bareme.lps)
            
            table.openWriteMode()
            table.setIndiv('ir_lps', ir_lps)
#            table.setIndiv('sal', sal+ir_lps)
            table.close_()

    def preproc_param(self, P):

        self.smic_h_b = P.cotsoc.gen.smic_h_b
        self.nbh_travaillees = 151.67*12     
        
        self.cho_seuil_exo = P.csg.chom.min_exo*self.nbh_travaillees*self.smic_h_b
        
        plaf_ss = 12*P.cotsoc.gen.plaf_ss
        
        #  Cotisations salariales
        sal = scaleBaremes(P.cotsoc.sal, plaf_ss)
        pat = scaleBaremes(P.cotsoc.pat, plaf_ss)
        csg = scaleBaremes(P.csg, plaf_ss)
        crds = scaleBaremes(P.crds, plaf_ss)
        
        # Création des dictionnaires de baremes cadre et noncadre à partir des barèmes communs
        sal.noncadre.__dict__.update(sal.commun.__dict__)
        sal.cadre.__dict__.update(sal.commun.__dict__)

        pat.noncadre.__dict__.update(pat.commun.__dict__)
        pat.cadre.__dict__.update(pat.commun.__dict__)

        pat.fonc.__dict__.update(pat.commun.__dict__)
        for var in ["apprentissage", "apprentissage2", "vieillesseplaf", "vieillessedeplaf", "formprof", "chomfg", "construction","assedic"]:
            del pat.fonc.__dict__[var]

        # TODO RAFP assiette = prime
        # TODO pension assiette = salaire hors prime
        # autres salaires + primes
        # TODO personnels non titulaires IRCANTEC etc
        
        # TODO contribution patronale de prévoyance complémentaire
        # Formation professionnelle (entreprise de 10 à moins de 20 salariés) salaire total 1,05%
        # Formation professionnelle (entreprise de moins de 10 salariés)      salaire total 0,55%
        # Taxe sur les salaries (pour ceux non-assujettis à la TVA)           salaire total 4,25% 
        # TODO accident du travail ?
 
        del sal.commun
        del pat.commun

        
        temp = 0
        if hasattr(P, "prelsoc"):
            for val in P.prelsoc.__dict__.itervalues(): temp += val
            P.prelsoc.total = temp         
        else : 
            P.__dict__.update({"prelsoc": {"total": 0} })
        
        a = {'sal':sal, 'pat':pat, 'csg':csg, 'crds':crds, 'exo_fillon': P.cotsoc.exo_fillon, 'lps': P.lps, 'ir': P.ir, 'prelsoc': P.prelsoc}
        return Dicts2Object(**a)

    def Crds(self, salbrut, P):
        '''
        CRDS sur les revenus selon le bareme fourni
        '''
        crds = - BarmMar(salbrut, P)
        return crds

def _cotsal(salbrut, hsup, cat, bareme):
    '''
    Cotisations sociales salariales
    '''
    n = len(salbrut)
    cotsal = np.zeros(n)
    for categ in salcats:
        iscat = (cat == getattr(CAT,categ))
        for bar in getattr(bareme.sal,categ).__dict__.itervalues():
            temp = - (iscat*BarmMar(salbrut-hsup, bar))
            cotsal += temp
    return cotsal

def _cotpat(salbrut, hsup, cat, bareme):
    '''
    Cotisation sociales patronales
    '''
    n = len(salbrut)
    cotpat = np.zeros(n)
    for categ in salcats:
        iscat = (cat == getattr(CAT,categ))
        for bar in getattr(bareme.pat,categ).__dict__.itervalues():
            temp = - (iscat*BarmMar(salbrut, bar))
            cotpat += temp
    return cotpat

def _alleg_fillon(salbrut):
    if categ == 'noncadre': # TODO: vérifier
        taux_fillon = tauxExoFillon(salbrut/self.nbh_travaillees, self.bareme.exo_fillon)
        alleg_fillon = taux_fillon*salbrut
    return alleg_fillon

def csgsald(salbrut, hsup, _P):
    '''
    CSG deductible sur les salaires
    '''
    P = _P.bareme.csg.act
    return - BarmMar(salbrut - hsup, P.deduc) 

def csgsali(salbrut, hsup, _P):
    '''
    CSG imposable sur les salaires
    '''
    P = _P.bareme.csg.act
    return  - BarmMar(salbrut - hsup, P.impos)

def CsgCho(self, chobrut):
    '''
    CSG sur les allocations chômage
    '''
    for categ in ("reduit","plein"):
        iscat = (self.csgTauxPlein & (categ=="plein"))
        for caisse, bareme in getattr(self.bareme.csg.chom,categ).__dict__.iteritems():
            if caisse=="deduc": csgchod = - (iscat*BarmMar(chobrut, bareme))
            else : csgchoi = - (iscat*BarmMar(chobrut, bareme)) 
            
    return csgchod,csgchoi

def CsgRst(self, rstbrut):
    '''
    CSG sur les pensions de retraite au sens strict
    '''
    for categ in ("reduit","plein"):
        iscat = (self.csgTauxPlein & (categ=="plein"))
        for caisse, bareme in getattr(self.bareme.csg.retraite, categ).__dict__.iteritems():
            if caisse=="deduc": csgrstd = - (iscat*BarmMar(rstbrut, bareme))
            else : csgrsti = - (iscat*BarmMar(rstbrut, bareme))
    return csgrstd, csgrsti                
    
def tauxExoFillon(self, salaire_horaire_brut, P):
    '''
    Exonération Fillon
    http://www.securite-sociale.fr/comprendre/dossiers/exocotisations/exoenvigueur/fillon.htm
    '''
    # TODO Ainsi, à compter du 1er juillet 2007, le taux d’exonération des employeurs de 19 salariés au plus
    # passera pour une rémunération horaire égale au SMIC de 26 % à 28,1 %.
    
    # TODO la divison par zéro engendre un warning
    # Le montant maximum de l’allègement dépend de l’effectif de l’entreprise. 
    # Le montant est calculé chaque année civile, pour chaque salarié ; 
    # il est égal au produit de la totalité de la rémunération annuelle telle que visée à l’article L. 242-1 du code de la Sécurité sociale par un coefficient. 
    # Ce montant est majoré de 10 % pour les entreprises de travail temporaire au titre des salariés temporaires pour lesquels elle est tenue à l’obligation 
    # d’indemnisation compensatrice de congés payés.
    if P.seuil <= 1:
        return 0 
    return P.tx_max*min_(1,max_(P.seuil*self.smic_h_b/(salaire_horaire_brut+1e-10)-1,0)/(P.seuil-1))

def impot_LPS(basecsg, nbF, nbH, statmarit, _P):
    '''
    Impôt individuel sur l'ensemble de l'assiette de la csg, comme proposé par
    Landais, Piketty, Saez (2011)
    '''
    P = _P.bareme.lps
    nbEnf = (nbF + nbH/2)
    ae = nbEnf*P.abatt_enfant
    re = nbEnf*P.reduc_enfant
    ce = nbEnf*P.credit_enfant

    couple = (statmarit == 1) | (statmarit == 5)
    ac = couple*P.abatt_conj
    rc = couple*P.reduc_conj

    return - max_(0, BarmMar(max_(basecsg - ae - ac, 0) , P.bareme)-re-rc) + ce

def _base_csg(salbrut, chobrut, rstbrut, rev_cap_bar, rev_cap_lib):
    return salbrut + chobrut + rstbrut + rev_cap_bar + rev_cap_lib

def _salbrut(sal, hsup, cat, _P):
    '''
    Calcule le salaire brut à partir du salaire net
    '''
    P = _P
    T = Object()
    T.noncadre = combineBaremes(P.sal.noncadre, name="noncadre_total")
    T.cadre    = combineBaremes(P.sal.cadre, name="cadre_total")
    T.fonc     = combineBaremes(P.sal.fonc, name="fonc_total")

    # On ajoute la CSG deductible
    T.noncadre.addBareme(P.csg.act.deduc)
    T.cadre.addBareme(P.csg.act.deduc)
    T.fonc.addBareme(P.csg.act.deduc)

    n = len(sal)
    tempdict ={}
    for categ, bar in T.__dict__.iteritems():
        tempdict.update({categ: bar.inverse()})
    bar = Dicts2Object(**tempdict)
    
    salbrut = np.zeros(n)

    for categ in salcats:
        brut = (cat == getattr(CAT,categ))*BarmMar(sal, getattr(bar, categ))
        salbrut += brut
    
    return salbrut + hsup
    
def _chobrut(cho, csgTauxPlein, _P):
    '''
    Calcule les allocations chômage brute à partir des allocations nettes
    '''
    P = _P.csg.chom
    T = Object()
    T.chom_plein = P.plein.deduc
    T.chom_reduit = P.reduit.deduc

    tempdict ={}
    for categ, bar in T.__dict__.iteritems():
        tempdict.update({categ: bar.inverse()})
    bar = Dicts2Object(**tempdict)

    chobrut =( not_(csgTauxPlein)*BarmMar(cho, bar.chom_reduit) + 
        csgTauxPlein*BarmMar(cho, bar.chom_plein) ) 

    return chobrut

def _rstbrut(rst, csgTauxPlein, _P):
    '''
    Calcule les pensions de retraites brutes à partir des pensions nettes
    '''
    P = _P.csg.retraite
    T = Object()

    T.retraite_plein = P.plein.deduc  # TODO rajouter la non  déductible dans param
    T.retraite_reduit = P.reduit.deduc  #

    tempdict ={}
    for categ, bar in T.__dict__.iteritems():
        tempdict.update({categ: bar.inverse()})
    bar = Dicts2Object(**tempdict)

    rstbrut = (not_(csgTauxPlein)*BarmMar(rst, bar.retraite_reduit) 
               + csgTauxPlein*BarmMar(rst, bar.retraite_plein))
    
    return rstbrut
     
def combineBaremes(BarColl, name="onsenfout"):
    baremeTot = Bareme(name=name)
    baremeTot.addTranche(0,0)
    for val in BarColl.__dict__.itervalues():
        if isinstance(val, Bareme):
            baremeTot.addBareme(val)
        else: 
            combineBaremes(val, baremeTot)
    return baremeTot

def scaleBaremes(BarColl, factor):
    out = Object()
    for key, val in BarColl.__dict__.iteritems():
        if isinstance(val, Bareme):
            setattr(out, key, val.multSeuils(factor))
        elif isinstance(val, Tree2Object):
            setattr(out, key, scaleBaremes(val, factor))
        else:
            setattr(out, key, val)
    return out
