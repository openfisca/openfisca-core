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
import numpy as np
from Config import CONF
from datetime import datetime

class CustomEnum(object):
    def __init__(self, varlist):
        self._vars = {}
        self._count = 0
        for var in varlist:
            self._vars.update({self._count:var})
            self._count += 1
        for key, var in self._vars.iteritems():
            setattr(self, var, key)
            
    def __getitem__(self, var):
        return getattr(self, var)

    def __iter__(self):
        return self.itervars()
    
    def itervars(self):
        for key, val in self._vars.iteritems():
            yield (val, key)


QUIFOY = CustomEnum(['vous', 'conj', 'pac1','pac2','pac3','pac4','pac5','pac6','pac7','pac8','pac9'])
QUIFAM = CustomEnum(['chef', 'part', 'enf1','enf2','enf3','enf4','enf5','enf6','enf7','enf8','enf9'])
QUIMEN = CustomEnum(['pref', 'cref', 'enf1','enf2','enf3','enf4','enf5','enf6','enf7','enf8','enf9'])
CAT    = CustomEnum(['noncadre', 'cadre', 'fonc'])

class CustomTable(object):
    def __init__(self, n):
        super(CustomTable, self).__init__()
        self.currentline = {}
        self.nrows = n
        self.count = 0
    
    def col(self, colname):
        return getattr(self, colname)
    
    def modifyColumn(self, column, colname):
        setattr(self, colname, column)
        
    def getWhereList(self, var, val, sort = False):
        
        a = self.col(var)
        out = np.argwhere(a == val)
        if sort: np.sort(out)
        return out

    def readCoordinates(self, coords, field):
        a = self.col(field)
        return a[coords]
    
    def flush(self):
        pass
    
    def row(self):
        return self.currentline
        
    def append(self):
        if self.count >= self.nrows:
            raise Exception('La table est pleine')
        for key, val in self.currentline.iteritems():
            a = getattr(self, key)
            a[self.count] = val
        self.currentline = {}
        self.count += 1
        
        
class PopulationTable(CustomTable):
# Informations sur les individus
    def __init__(self, n):
        super(PopulationTable, self).__init__(n)
        self.noi         = np.zeros(n, dtype=np.uint)     # unique dans un ménage
        self.birth       = np.array(["9999-01-01"]*n)
        self.quifoy      = np.zeros(n, dtype=np.uint8) 
        self.quifam      = np.zeros(n, dtype=np.uint8)
        self.quimen      = np.zeros(n, dtype=np.uint8)
        self.idmen       = np.zeros(n, dtype=np.uint)       # 600001, 600002,
        self.idfoy       = np.zeros(n, dtype=np.uint)       # idmen + noi du déclarant
        self.idfam       = np.zeros(n, dtype=np.uint)       # idmen + noi du chef de famille
        self.statmarit   = 2*np.ones(n, dtype=np.int8)# 1: marie, 2: celibataire, 3: divorcé, 4 veuf, 5 pacsé
        self.age         = -9999*np.ones(n, dtype=np.int32) # age au premier janvier
        self.agem        = -9999*np.ones(n, dtype=np.int32) # age en mois à la date de la simulation
        self.inv         = np.zeros(n, dtype=np.uint)       # Invalide
        self.alt         = np.zeros(n, dtype=np.uint)       # Garde alterné
        self.activite    = np.zeros(n, dtype=np.int8)      # actif occupé 0, chômeur 1, étudiant/élève 2, retraité 3, autre inactif 4
    
    # Salaire
        self.cotsal       = np.zeros(n, dtype=np.float32)     # Cotisations sociales salariales
        self.csgactd      = np.zeros(n, dtype=np.float32)     # CSG déductible sur les revenus d'activité
        self.csgacti      = np.zeros(n, dtype=np.float32)     # CSG non déductible sur les revenus d'activité
        self.crdsact      = np.zeros(n, dtype=np.float32)     # CRDS (non déductible) sur les revenus d'activité
        self.cotpat       = np.zeros(n, dtype=np.float32)     # Cotisations sociales patronales
        self.alleg_fillon = np.zeros(n, dtype=np.float32)     # Allègement de charge Fillon
        self.salsuperbrut = np.zeros(n, dtype=np.float32)     # Salaires super bruts (coût du travail)
        self.salbrut      = np.zeros(n, dtype=np.float32)     # Salaires bruts
        self.sal          = np.zeros(n, dtype=np.float32)     # Salaires (Revenus d'activité)
        self.cat          = np.zeros(n, dtype=np.uint8)
        
    # Chômage
        self.csgTauxPlein = np.ones(n, dtype=np.bool)           # Cotisations sociales salariales
        self.csgchod      = np.zeros(n, dtype=np.float32)       # CSG déductible sur les revenus de remplacement constitué par les indemnités chômage
        self.csgchoi      = np.zeros(n, dtype=np.float32)       # CSG non déductible sur les revenus de remplacement constitué par les indemnités chômage
        self.crdscho      = np.zeros(n, dtype=np.float32)       # CRDS sur les revenus de remplacement constitué par les indemnités chômage
        self.exo_cho      = np.zeros(n, dtype=np.float32)       # Exonération de CSG et de CRDS sur les revenus de remplacement constitué par les indemnités chômage
        self.chobrut      = np.zeros(n, dtype=np.float32)       # Autres revenus (allocations chômage brut de csg déductible)
        self.cho          = np.zeros(n, dtype=np.float32)           # Autres revenus (allocations chômage)
        
    # Retraite
        self.csgrstd = np.zeros(n, dtype=np.float32) # CSG déductible sur les revenus de remplacement constitué par les pensions et retraites au sens strict
        self.csgrsti = np.zeros(n, dtype=np.float32) # CSG non déductible sur les revenus de remplacement constitué par les pensions et retraites au sens strict
        self.crdsrst = np.zeros(n, dtype=np.float32) # CRDS sur les revenus de remplacement constitué par les pensions et retraites au sens strict
        self.rstbrut = np.zeros(n, dtype=np.float32) # retraites au sens strict (pensions de retraite, d’invalidité, et les rentes viagères à titre gratuit) 
        self.rst     = np.zeros(n, dtype=np.float32) # retraites au sens strict
        self.alr     = np.zeros(n, dtype=np.float32) # pensions reçues
        self.rto     = np.zeros(n, dtype=np.float32) # rentes viagères à titre onéreux
        
        self.basecsg = np.zeros(n, dtype=np.float32) # Assiette de la Csg
        self.ir_lps  = np.zeros(n, dtype=np.float32) # Impôt sur le revenu après fusion IR-CSG individuelle à la Landais, Piketty, Saez
                                           
    # Revenus du capital
        self.csgcap_bar       = np.zeros(n, dtype=np.float32)       # csg sur les revenus du capital soumis au barème 
        self.prelsoccap_bar   = np.zeros(n, dtype=np.float32)       # Prélèvement social et contribution additionnelle des revenus du capital soumis au barème
        self.crdscap_bar      = np.zeros(n, dtype=np.float32)       # Contribution au remboursement de la dette sociale des revenus du capital soumis au barème
        self.csgcap_lib       = np.zeros(n, dtype=np.float32)       # csg sur les revenus du capital soumis au prélèvement libératoire
        self.prelsoccap_lib   = np.zeros(n, dtype=np.float32)       # Prélèvement social et contribution additionnelle des revenus du capital soumis au prélèvement libératoire 
        self.crdscap_lib      = np.zeros(n, dtype=np.float32)       # Contribution au remboursement de la dette sociale des revenus du capital soumis au prélèvement libératoire 
        self.revcap_lib       = np.zeros(n, dtype=np.float32)       # revenus de valeurs mobilières soumis au prélèvement libératoire
        self.revcap_bar       = np.zeros(n, dtype=np.float32)       # revenu des capitaux mobiliers soumis au barème
        
        self.produitfin_i  = np.zeros(n, dtype=np.float32)
        self.csgfin_i      = np.zeros(n, dtype=np.float32)
        
    # Élself.éments individualisé de la déclaration de revenu
        self.fra         = np.zeros(n, dtype=np.float32)  # Frais professionnel
        self.choCheckBox = np.zeros(n, dtype=np.bool) #
        self.hsup        = np.zeros(n, dtype=np.float32)  # Heures supplémentaires exonérées
        self.mhsup        = np.zeros(n, dtype=np.float32)  # Heures supplémentaires exonérées
        self.ppeCheckBox = np.zeros(n, dtype=np.bool) # Case 'vous avez travaillé à temps plein toute l'année'
        self.ppeHeure    = np.zeros(n, dtype=np.int32)  #
        self.avf         = np.zeros(n, dtype=np.float32)  #  
        self.glo         = np.zeros(n, dtype=np.float32)  #  gain de levée d'option
        self.quo         = np.zeros(n, dtype=np.float32)  #
        self.etr         = np.zeros(n, dtype=np.float32)  #
        self.tspr        = np.zeros(n, dtype=np.float32)  # revenu catégoriel: total salaires, pensions et rentes
        self.fon         = np.zeros(n, dtype=np.float32)  # revenus fonciers après abatement et soustraction des deficits 
        self.rfon        = np.zeros(n, dtype=np.float32)  # revenus fonciers
        self.rpns        = np.zeros(n, dtype=np.float32)  # revenu catégoriel: revenu des professions non salariés
        self.rag         = np.zeros(n, dtype=np.float32)  # revenus agricoles
        self.ric         = np.zeros(n, dtype=np.float32)  # revenus industriels et commerciaux    
        self.rac         = np.zeros(n, dtype=np.float32)  # revenus accessoires
        self.rnc         = np.zeros(n, dtype=np.float32)  # revenus non commerciaux
        self.alv         = np.zeros(n, dtype=np.float32)  #
        self.ppe         = np.zeros(n, dtype=np.float32)  # prime pour l'emploi
        self.div         = np.zeros(n, dtype=np.float32)  #
        
        self.div_rmi     = np.zeros(n, dtype=np.int32)    #
        self.revColl     = np.zeros(n, dtype=np.int32)    #
        self.asf_elig    = np.zeros(n, dtype=np.int32)    #
        self.al_nbinv    = np.zeros(n, dtype=np.int32)    #
        
    # Impôt
        self.imp_lib     = np.zeros(n, dtype=np.float32)      # Prélèvement libératoire
        self.irpp        = np.zeros(n, dtype=np.float32)      # Impôt sur le revenu
        self.thab        = np.zeros(n, dtype=np.float32)      # Taxe d'habitation
    
    # prestations familiales
        self.af          = np.zeros(n, dtype=np.float32) # Allocation familiale
        self.cf          = np.zeros(n, dtype=np.float32) # Complément familial
        self.aeeh        = np.zeros(n, dtype=np.float32) # Allocation d'éducation de l'enfant handicapé
        self.paje        = np.zeros(n, dtype=np.float32) # Prestation d'accueil du jeune enfant (Base)
        self.nais        = np.zeros(n, dtype=np.float32) # Prestation d'accueil du jeune enfant (Prime de naissance)
        self.clca        = np.zeros(n, dtype=np.float32) # Prestation d'accueil du jeune enfant (CLCA)
        self.colca       = np.zeros(n, dtype=np.float32) # Prestation d'accueil du jeune enfant (COLCA)
        self.clmg        = np.zeros(n, dtype=np.float32) # Prestation d'accueil du jeune enfant (CLMG)
        self.asf         = np.zeros(n, dtype=np.float32) # Allocation de soutien familial
        self.ars         = np.zeros(n, dtype=np.float32) # Allocation de rentrée scolaire
        self.ape         = np.zeros(n, dtype=np.float32) # Allocation parentale d'éducation
        self.apje        = np.zeros(n, dtype=np.float32) # Allocation pour jeune enfant
    
    # Information sur le logement
        self.so          = 3*np.ones(n, dtype=np.int8)
        self.zone_apl    = 2*np.ones(n, dtype=np.int8)
        self.loyer       = np.zeros(n, dtype=np.uint)
    
    # allocations logements
        self.als         = np.zeros(n, dtype=np.float32) # Allocation de logement social
        self.alf         = np.zeros(n, dtype=np.float32) # Allocation de logement famillial
        self.alset       = np.zeros(n, dtype=np.float32) # Allocation logement (étudiant)
        self.apl         = np.zeros(n, dtype=np.float32) # Aide personnalisée au logement
    
    # minima sociaux
        self.mv          = np.zeros(n, dtype=np.float32) # Minimum vieillesse
        self.asi         = np.zeros(n, dtype=np.float32) # Allocation supplémentaire d'invalidité
        self.aah         = np.zeros(n, dtype=np.float32) # Allocation adulte handicapé
        self.caah        = np.zeros(n, dtype=np.float32) # Complément de l'allocation adulte handicapé
        self.api         = np.zeros(n, dtype=np.float32) # Allocation de parent isolé
        self.rsa         = np.zeros(n, dtype=np.float32) # Revenu minimum d'insertion
        self.rsaact      = np.zeros(n, dtype=np.float32) # Complément d'activité du RSA
        self.aefa        = np.zeros(n, dtype=np.float32) # Aide exceptionnelle de fin d'année
        

class FoyerTable(CustomTable):
# Situations particulières
    def __init__(self, n):
        super(FoyerTable, self).__init__(n)
        self.caseX = np.zeros(n, dtype = bool)
        self.caseY = np.zeros(n, dtype = bool)
        self.caseZ = np.zeros(n, dtype = bool)
        self.caseK = np.zeros(n, dtype = bool) 
        self.caseE = np.zeros(n, dtype = bool)
        self.caseH = np.zeros(n, dtype = bool)
        self.caseN = np.zeros(n, dtype = bool)
        self.caseL = np.zeros(n, dtype = bool)
        self.caseP = np.zeros(n, dtype = bool)
        self.caseF = np.zeros(n, dtype = bool)
        self.caseW = np.zeros(n, dtype = bool)
        self.caseS = np.zeros(n, dtype = bool)
        self.caseG = np.zeros(n, dtype = bool)
        self.caseT = np.zeros(n, dtype = bool)
    
    # Personnes à charge
        self.nbF = np.zeros(n, dtype = np.int8) # nombre d'enfants en résidence exclusive 
        self.nbH = np.zeros(n, dtype = np.int8) # nombre d'enfants en résidence alternée 
        self.nbG = np.zeros(n, dtype = np.int8) # nombre d'enfants en résidence exclusive invalides 
        self.nbI = np.zeros(n, dtype = np.int8) # nombre d'enfants en résidence alternée invalides
        self.nbJ = np.zeros(n, dtype = np.int8) # nombre d'enfants majeurs rattachés
        self.nbR = np.zeros(n, dtype = np.int8) # nombre personnes titulaires de la carte d'invalité d'au moins 80 # 
        self.nbN = np.zeros(n, dtype = np.int8) # nombre d'enfants chargés de famille rattachés
        
    # Retes à titre onéreux
        self.f1aw = np.zeros(n, dtype = int)
        self.f1bw = np.zeros(n, dtype=np.int32)
        self.f1cw = np.zeros(n, dtype=np.int32)
        self.f1dw = np.zeros(n, dtype=np.int32)
    
    # Revenus des valeurs et capitaux mobiliers
        self.f2da = np.zeros(n, dtype=np.int32)
        self.f2dh = np.zeros(n, dtype=np.int32)
        self.f2ee = np.zeros(n, dtype=np.int32)
        
        self.f2dc = np.zeros(n, dtype=np.int32)
        self.f2fu = np.zeros(n, dtype=np.int32)
        self.f2ch = np.zeros(n, dtype=np.int32)
        self.f2ts = np.zeros(n, dtype=np.int32)
        self.f2go = np.zeros(n, dtype=np.int32)
        self.f2tr = np.zeros(n, dtype=np.int32)
        
        self.f2cg = np.zeros(n, dtype=np.int32)
        self.f2bh = np.zeros(n, dtype=np.int32)
        self.f2ca = np.zeros(n, dtype=np.int32)
        self.f2ab = np.zeros(n, dtype=np.int32)
        self.f2aa = np.zeros(n, dtype=np.int32)
        self.f2al = np.zeros(n, dtype=np.int32)
        self.f2am = np.zeros(n, dtype=np.int32)
        self.f2an = np.zeros(n, dtype=np.int32)
        
    # Plus values et gains taxables à 18 %
        self.f3vg = np.zeros(n, dtype=np.int32)
        self.f3vh = np.zeros(n, dtype=np.int32)
        self.f3vt = np.zeros(n, dtype=np.int32)
        self.f3vu = np.zeros(n, dtype=np.int32)
        self.f3vv = np.zeros(n, dtype=np.int32)
        
    # Revenus fonciers
        self.f4ba = np.zeros(n, dtype=np.int32)
        self.f4bb = np.zeros(n, dtype=np.int32)
        self.f4bc = np.zeros(n, dtype=np.int32)
        self.f4bd = np.zeros(n, dtype=np.int32)
        self.f4be = np.zeros(n, dtype=np.int32)
        self.f4bf = np.zeros(n, dtype=np.int32)
        
    # Déficits antérieurs
        self.f6de = np.zeros(n, dtype=np.int32)
        self.f6gi = np.zeros(n, dtype=np.int32)
        self.f6gj = np.zeros(n, dtype=np.int32)
        self.f6el = np.zeros(n, dtype=np.int32)
        self.f6em = np.zeros(n, dtype=np.int32)
        self.f6gp = np.zeros(n, dtype=np.int32)
        self.f6gu = np.zeros(n, dtype=np.int32)
        self.f6dd = np.zeros(n, dtype=np.int32)
        
        self.f6fa = np.zeros(n, dtype=np.int32)
        self.f6fb = np.zeros(n, dtype=np.int32)
        self.f6fc = np.zeros(n, dtype=np.int32)
        self.f6fd = np.zeros(n, dtype=np.int32)
        self.f6fe = np.zeros(n, dtype=np.int32)
        self.f6fl = np.zeros(n, dtype=np.int32)
        
        self.f6eu = np.zeros(n, dtype=np.int32)
        self.f6ev = np.zeros(n, dtype=np.int32)
        
        self.f6cb = np.zeros(n, dtype=np.int32)
        self.f6hj = np.zeros(n, dtype=np.int32)
        
        self.f6gh = np.zeros(n, dtype=np.int32)
        
    # réduction et crédit d'impôt
        self.f7ud = np.zeros(n, dtype=np.int32)
        self.f7uf = np.zeros(n, dtype=np.int32)
        
        self.f7xs = np.zeros(n, dtype=np.int32)
        self.f7xt = np.zeros(n, dtype=np.int32)
        self.f7xu = np.zeros(n, dtype=np.int32)
        self.f7xw = np.zeros(n, dtype=np.int32)
        self.f7xy = np.zeros(n, dtype=np.int32)
        
        self.f7ac = np.zeros(n, dtype=np.int32)
        self.f7ae = np.zeros(n, dtype=np.int32)
        self.f7ag = np.zeros(n, dtype=np.int32)
    
        self.f7db = np.zeros(n, dtype=np.int32)
        self.f7df = np.zeros(n, dtype=np.int32)
        self.f7dq = np.zeros(n, dtype=np.int32)
        self.f7dg = np.zeros(n, dtype=np.int32)
        self.f7dl = np.zeros(n, dtype=np.int32)
        
        self.f7vy = np.zeros(n, dtype=np.int32)
        self.f7vz = np.zeros(n, dtype=np.int32)
        self.f7vw = np.zeros(n, dtype=np.int32)
        self.f7vx = np.zeros(n, dtype=np.int32)
        
        self.f7cd = np.zeros(n, dtype=np.int32)
        self.f7ce = np.zeros(n, dtype=np.int32)
    
        self.f7ga = np.zeros(n, dtype=np.int32)
        self.f7gb = np.zeros(n, dtype=np.int32)
        self.f7gc = np.zeros(n, dtype=np.int32)
        self.f7ge = np.zeros(n, dtype=np.int32)
        self.f7gf = np.zeros(n, dtype=np.int32)
        self.f7gg = np.zeros(n, dtype=np.int32)
        
        self.f7ea = np.zeros(n, dtype=np.int32)
        self.f7eb = np.zeros(n, dtype=np.int32)
        self.f7ec = np.zeros(n, dtype=np.int32)
        self.f7ed = np.zeros(n, dtype=np.int32)
        self.f7ef = np.zeros(n, dtype=np.int32)
        self.f7eg = np.zeros(n, dtype=np.int32)
        
        self.f7gz = np.zeros(n, dtype=np.int32)
        
        self.f7uk = np.zeros(n, dtype=np.int32)
        self.f7vo = np.zeros(n, dtype=np.int32)
        self.f7td = np.zeros(n, dtype=np.int32)
        
        self.f7wn = np.zeros(n, dtype=np.int32)
        self.f7wo = np.zeros(n, dtype=np.int32)
        self.f7wm = np.zeros(n, dtype=np.int32)
        self.f7wp = np.zeros(n, dtype=np.int32)
    
        self.f7we = np.zeros(n, dtype=np.int32)
        self.f7wq = np.zeros(n, dtype=np.int32)
        self.f7wh = np.zeros(n, dtype=np.int32)
        self.f7wk = np.zeros(n, dtype=np.int32)
        self.f7wf = np.zeros(n, dtype=np.int32)
        
        self.f7wi = np.zeros(n, dtype=np.int32)
        self.f7wj = np.zeros(n, dtype=np.int32)
        self.f7wl = np.zeros(n, dtype=np.int32)
        
    ############
    ### non accessible à l'utilisateur
        self.f1tv = np.zeros(n, dtype=np.int32)
        self.f1tw = np.zeros(n, dtype=np.int32)
        self.f1tx = np.zeros(n, dtype=np.int32)
        self.f1uv = np.zeros(n, dtype=np.int32)
        self.f1uw = np.zeros(n, dtype=np.int32)
        self.f1ux = np.zeros(n, dtype=np.int32)
        
        self.f1aq = np.zeros(n, dtype=np.int32)
        self.f1bq = np.zeros(n, dtype=np.int32)
        self.f1lz = np.zeros(n, dtype=np.int32)
        self.f1mz = np.zeros(n, dtype=np.int32)
        
        self.f2bg = np.zeros(n, dtype=np.int32)
        self.f2dm = np.zeros(n, dtype=np.int32)
        
        self.f3va = np.zeros(n, dtype=np.int32)
        self.f3vc = np.zeros(n, dtype=np.int32)
        self.f3vd = np.zeros(n, dtype=np.int32)    
        self.f3ve = np.zeros(n, dtype=np.int32)    
        self.f3vf = np.zeros(n, dtype=np.int32)
        self.f3vi = np.zeros(n, dtype=np.int32)
        self.f3vj = np.zeros(n, dtype=np.int32)
        self.f3vk = np.zeros(n, dtype=np.int32)
        self.f3vl = np.zeros(n, dtype=np.int32)
        self.f3vm = np.zeros(n, dtype=np.int32)
        
        self.f4bl = np.zeros(n, dtype=np.int32)
        self.f4tq = np.zeros(n, dtype=np.int32)
        self.f4ga = np.zeros(n, dtype=np.int32)
        self.f4gb = np.zeros(n, dtype=np.int32)
        self.f4gc = np.zeros(n, dtype=np.int32)
        self.f4ge = np.zeros(n, dtype=np.int32)
        self.f4gf = np.zeros(n, dtype=np.int32)
        self.f4gg = np.zeros(n, dtype=np.int32)
        
        self.f5nv = np.zeros(n, dtype=np.int32)
        self.f5ov = np.zeros(n, dtype=np.int32)
        self.f5pv = np.zeros(n, dtype=np.int32)
        self.f5nw = np.zeros(n, dtype=np.int32)
        self.f5ow = np.zeros(n, dtype=np.int32)
        self.f5pw = np.zeros(n, dtype=np.int32)
        
        self.f5qm = np.zeros(n, dtype=np.int32)
        self.f5rm = np.zeros(n, dtype=np.int32)
        
        self.f6ps = np.zeros(n, dtype=np.int32)
        self.f6rs = np.zeros(n, dtype=np.int32)
        self.f6ss = np.zeros(n, dtype=np.int32)
        self.f6ps = np.zeros(n, dtype=np.int32)
        self.f6rs = np.zeros(n, dtype=np.int32)
        self.f6ss = np.zeros(n, dtype=np.int32)
        self.f6ps = np.zeros(n, dtype=np.int32)
        self.f6rs = np.zeros(n, dtype=np.int32)
        self.f6ss = np.zeros(n, dtype=np.int32)
        
        self.f7ra = np.zeros(n, dtype=np.int32)
        self.f7rb = np.zeros(n, dtype=np.int32)
        self.f7ka = np.zeros(n, dtype=np.int32)
        self.f7gs = np.zeros(n, dtype=np.int32)
        self.f7um = np.zeros(n, dtype=np.int32)
        self.f7gq = np.zeros(n, dtype=np.int32)
        self.f7fq = np.zeros(n, dtype=np.int32)
        self.f7fm = np.zeros(n, dtype=np.int32)
        self.f7nz = np.zeros(n, dtype=np.int32)
        self.f7gn = np.zeros(n, dtype=np.int32)
        self.f7fn = np.zeros(n, dtype=np.int32)
        self.f7cf = np.zeros(n, dtype=np.int32)
        self.f7cl = np.zeros(n, dtype=np.int32)
        self.f7cm = np.zeros(n, dtype=np.int32)
        self.f7cn = np.zeros(n, dtype=np.int32)
        self.f7cu = np.zeros(n, dtype=np.int32)
        self.f7fh = np.zeros(n, dtype=np.int32)
        self.f7un = np.zeros(n, dtype=np.int32)
        self.f7uc = np.zeros(n, dtype=np.int32)
    
        self.f7xc = np.zeros(n, dtype=np.int32)
        self.f7xd = np.zeros(n, dtype=np.int32)
        self.f7xe = np.zeros(n, dtype=np.int32)
        self.f7xf = np.zeros(n, dtype=np.int32)
        self.f7xg = np.zeros(n, dtype=np.int32)
        self.f7xh = np.zeros(n, dtype=np.int32)
        self.f7xi = np.zeros(n, dtype=np.int32)
        self.f7xj = np.zeros(n, dtype=np.int32)
        self.f7xk = np.zeros(n, dtype=np.int32)
        self.f7xl = np.zeros(n, dtype=np.int32)
        self.f7xm = np.zeros(n, dtype=np.int32)
        self.f7xn = np.zeros(n, dtype=np.int32)
        self.f7xo = np.zeros(n, dtype=np.int32)
        
        self.f7qb = np.zeros(n, dtype=np.int32)
        self.f7qc = np.zeros(n, dtype=np.int32)
        self.f7qd = np.zeros(n, dtype=np.int32)
        self.f7ql = np.zeros(n, dtype=np.int32)
        self.f7qt = np.zeros(n, dtype=np.int32)
        self.f7qm = np.zeros(n, dtype=np.int32)
        self.f7ff = np.zeros(n, dtype=np.int32)
        self.f7fg = np.zeros(n, dtype=np.int32)
        self.f7jy = np.zeros(n, dtype=np.int32)
        self.f7fy = np.zeros(n, dtype=np.int32)
        self.f7gy = np.zeros(n, dtype=np.int32)
        self.f7hy = np.zeros(n, dtype=np.int32)
        self.f7iy = np.zeros(n, dtype=np.int32)
        self.f7ly = np.zeros(n, dtype=np.int32)
        self.f7ky = np.zeros(n, dtype=np.int32)
        self.f7my = np.zeros(n, dtype=np.int32)
        self.f7ur = np.zeros(n, dtype=np.int32)
        self.f7oz = np.zeros(n, dtype=np.int32)
        self.f7pz = np.zeros(n, dtype=np.int32)
        self.f7qz = np.zeros(n, dtype=np.int32)
        self.f7rz = np.zeros(n, dtype=np.int32)
        self.f7sz = np.zeros(n, dtype=np.int32)
    
        self.f7uo = np.zeros(n, dtype=np.int32)
        self.f7us = np.zeros(n, dtype=np.int32)
        self.f7sf = np.zeros(n, dtype=np.int32)
        self.f7sb = np.zeros(n, dtype=np.int32)
        self.f7sd = np.zeros(n, dtype=np.int32)
        self.f7se = np.zeros(n, dtype=np.int32)
        self.f7sh = np.zeros(n, dtype=np.int32)
        
        self.f8tb = np.zeros(n, dtype=np.int32)
        self.f8tc = np.zeros(n, dtype=np.int32)
        self.f8te = np.zeros(n, dtype=np.int32)
        self.f8tf = np.zeros(n, dtype=np.int32)
        self.f8tg = np.zeros(n, dtype=np.int32)
        self.f8to = np.zeros(n, dtype=np.int32)
        self.f8tp = np.zeros(n, dtype=np.int32)
        self.f8th = np.zeros(n, dtype=np.int32)
        self.f8uz = np.zeros(n, dtype=np.int32)
        self.f8tz = np.zeros(n, dtype=np.int32)
        self.f8wa = np.zeros(n, dtype=np.int32)
        self.f8wb = np.zeros(n, dtype=np.int32)
        self.f8wd = np.zeros(n, dtype=np.int32)
        self.f8we = np.zeros(n, dtype=np.int32)
        self.f8wr = np.zeros(n, dtype=np.int32)
        self.f8wt = np.zeros(n, dtype=np.int32)
        self.f8wu = np.zeros(n, dtype=np.int32)
        self.f8wv = np.zeros(n, dtype=np.int32)
                
# Pour les années avant 2010 en remontant le temps
# 2009    
        self.f7uh = np.zeros(n, dtype=np.int32)
        self.f8ta = np.zeros(n, dtype=np.int32)
        self.f8ws = np.zeros(n, dtype=np.int32)
        self.f8wx = np.zeros(n, dtype=np.int32)                       
        self.f8wy = np.zeros(n, dtype=np.int32)                       

        self.f2gr = np.zeros(n, dtype=np.int32)
        self.f7wg = np.zeros(n, dtype=np.int32)
        self.f7sc = np.zeros(n, dtype=np.int32)

# 2008
        self.f6eh = np.zeros(n, dtype=np.int32)
        self.f7ui = np.zeros(n, dtype=np.int32) 
        self.f8wc = np.zeros(n, dtype=np.int32) 
        self.f1ar = np.zeros(n, dtype=np.int32) 
        self.f1ar = np.zeros(n, dtype=np.int32) 
        self.f1br = np.zeros(n, dtype=np.int32) 
        self.f1cr = np.zeros(n, dtype=np.int32) 
        self.f1dr = np.zeros(n, dtype=np.int32) 
        self.f1er = np.zeros(n, dtype=np.int32) 

# 2007
        self.f7ua = np.zeros(n, dtype=np.int32)
        self.f7ub = np.zeros(n, dtype=np.int32)
        self.f7uj = np.zeros(n, dtype=np.int32)
        self.f7up = np.zeros(n, dtype=np.int32)
        self.f7uq = np.zeros(n, dtype=np.int32)
        
# 2006
        self.f6da = np.zeros(n, dtype=np.int32)
        self.f6cc = np.zeros(n, dtype=np.int32)
                   
# 2005
        self.f6aa = np.zeros(n, dtype=np.int32)                   
        self.f8td = np.zeros(n, dtype=np.int32)                   

# 2004
        self.f7gw = np.zeros(n, dtype=np.int32)                           
        self.f7gx = np.zeros(n, dtype=np.int32)                           
                   
class Population(object):
    '''
    La classe Population est un wrapper pour une PyTable qui permet de créer des individus, et de reconstituer 
    des familles, des ménages et des foyers à partir des champs de la table.
    '''
    def __init__(self):
        super(Population, self).__init__()
        self.readMode = False
        self.writeMode = False
        
    def initialize(self, scenario):
        self.datesim = datetime.strptime(CONF.get('simulation', 'datesim') ,"%Y-%m-%d").date()
        self.year = self.datesim.year
        self.NMEN = CONF.get('simulation', 'nmen')
        self.MAXREV = CONF.get('simulation', 'maxrev')
        self.XAXIS = CONF.get('simulation', 'xaxis')
        self.scenario = scenario
        n = len(self.scenario.indiv)

        self.table = PopulationTable(n*self.NMEN)
        self.foyer = FoyerTable(n*self.NMEN)
        self.createIndividus(self.scenario)
        
        self.createSorters(['men', 'fam', 'foy'])
        
        self.createFoyer(self.scenario)
        
        self.nbenfmax = 9

    def createSorters(self, unitlist):
        '''
        crée des vecteurs d'indices pour récupérer les individus en fonction de leur 
        foyer, famille, ou menage.
        '''
        self.nbInd = self.table.nrows
        self.index = {}
        for unit in unitlist:
            list = np.unique(self.table.col('id' + unit))
            setattr(self, 'nb' + unit.capitalize(), len(list))

            if unit == 'foy': ENUM = QUIFOY
            elif unit == 'men': ENUM = QUIMEN
            elif unit == 'fam': ENUM = QUIFAM

            self.index.update({unit: {}})
            dct = self.index[unit]
            for person in ENUM:
                idxIndi = self.table.getWhereList('qui' + unit, person[1], sort = True).squeeze()
                indice = self.table.readCoordinates(idxIndi, field = 'id' + unit)
                idxUnit = np.searchsorted(list, indice)
                temp = {'idxIndi':idxIndi, 'idxUnit':idxUnit}
                dct.update({person[0]:temp})

        self.scenar2foy = {}
        decl = self.table.col('quifoy') == 0
        for i in xrange(len(self.scenario.indiv)):
            temp = self.table.col('noi') == i
            idxIndiv = np.sort(np.argwhere(temp & decl))
            self.scenar2foy.update({i: idxIndiv})
                
    def openWriteMode(self, fields = None):
        if self.writeMode or self.readMode:
            raise Exception(u'La table est déjà ouverte')
        self.writeMode = True
            
    def openReadMode(self, fields = None):
        if self.writeMode or self.readMode:
            raise Exception(u'La table est déjà ouverte')        
        self.readMode = True

    def close_(self):
        if not (self.writeMode or self.readMode):
            raise Exception(u"La table n'est pas ouverte")
        self.writeMode = False
        self.readMode = False

    def getIndiv(self, varstring, base = 'individu'):
        if not self.readMode:
            raise Exception('This instance shoud be on readMode, see openReadMode')
        if base == 'individu': table = self.table
        elif base == 'foyer': table = self.foyer
        return table.col(varstring)

    def setIndiv(self, varstring, value):
        self.table.modifyColumn(column=value , colname = varstring)
        self.table.flush()

    def get(self, qui, varstring, unit, base = 'individu', sumqui = False, default = 0):
        if not self.readMode: raise Exception('This instance shoud be on readMode, see openReadMode')
        out = []
        nb = getattr(self, 'nb'+ unit.capitalize())
        if base == 'individu': var = self.table.col(varstring)
        elif base == 'foyer': var = self.foyer.col(varstring)
        checkType = isinstance(qui,str)
        if checkType: qui = [qui]
        for person in qui:
            temp = np.ones(nb, dtype = var.dtype)*default
            idx = self.index[unit][person]
            temp[idx['idxUnit']] = var[idx['idxIndi']]
            out.append(temp)
        if checkType : return out[0]
        elif sumqui:  return np.sum(np.array(out), axis = 0)
        else: return out

    def set(self, qui, varstring, value, unit):
        if not self.writeMode: raise Exception('This instance shoud be on writeMode, see openWriteMode')
        table = self.table
        idx = self.index[unit][qui]
        var = table.col(varstring)
        var[idx['idxIndi']] = np.array(value, dtype = var.dtype)[idx['idxUnit']]
        table.modifyColumn(column=var , colname = varstring)
        table.flush()
                
    def setColl(self, varstring, value):
        '''
        pour affecter les revenus non individualisable aux individu.
        ici on donne tout à vous
        '''
        self.set('vous',varstring, value, 'foy')
                
    def createIndividus(self, scenario):
        # pour l'instant, un seul menage répliqué n fois
        for noi, person in scenario.indiv.iteritems():
            if noi==0: loyer = scenario.menage[noi]['loyer']
            else: loyer = 0
            so = scenario.menage[person['noipref']]['so']
            zone_apl = scenario.menage[person['noipref']]['zone_apl']

            self.addPerson(noi = noi,
                           loyer = loyer,
                           so = so,
                           zone_apl = zone_apl,
                           xaxis = self.XAXIS,
                           **person)

    def addPerson(self, noi, xaxis,  birth, loyer, zone_apl, so, quifoy, quifam, quimen, noidec, noichef, noipref, inv, alt, activite, statmarit=0, sal =0, cho =0, rst = 0, choCheckBox = 0, hsup = 0, ppeCheckBox = 0, ppeHeure = 0, **kwargs):
        for i in xrange(self.NMEN):
            indiv = self.table.row()
            indiv['noi']   = noi
            indiv['birth'] = birth.isoformat()
            indiv['loyer'] = loyer
            indiv['zone_apl'] = zone_apl
            indiv['so'] = so
            indiv['quifoy'] = QUIFOY[quifoy]
            indiv['quifam'] = QUIFAM[quifam]
            indiv['quimen'] = QUIMEN[quimen]
            indiv['idmen'] = 60000 + i + 1 
            indiv['idfoy'] = indiv['idmen']*100 + noidec
            indiv['idfam'] = indiv['idmen']*100 + noichef
            indiv['statmarit'] = statmarit
            indiv['activite'] = activite
            indiv['age'] = self.year- birth.year
            indiv['agem'] = 12*(self.datesim.year- birth.year) + self.datesim.month - birth.month
            indiv['choCheckBox'] = choCheckBox
            indiv['hsup'] = hsup
            indiv['ppeCheckBox'] = ppeCheckBox
            indiv['ppeHeure'] = ppeHeure
            indiv['sal'] = sal
            indiv['cho'] = cho
            indiv['rst'] = rst
            if (noi == 0) and (self.NMEN > 1):
                var = i/(self.NMEN-1)*self.MAXREV
                indiv[xaxis] = var
            indiv['inv'] = inv
            indiv['alt'] = alt

            self.table.append()
        self.table.flush()

    def createFoyer(self, scenario):
        # on crée des lignes vides
        row = self.foyer.row()
        for i in xrange(self.nbInd):
            self.foyer.append()
        self.foyer.flush()

        for noidec, vals in scenario.declar.iteritems():
            for var, val in vals.iteritems():
                if val != 0:
                    idx = self.scenar2foy[noidec]
                    oldvar = np.array(self.foyer.col(var), dtype = int)
                    temp   = np.ones(len(idx), dtype = int)*val
                    oldvar[idx] = temp
                    self.foyer.modifyColumn(column=oldvar , colname = var)
        self.foyer.flush()
        