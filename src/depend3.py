# -*- coding: utf-8 -*-
from __future__ import division
from core.datatable import DataTable, IntCol, BoolCol, FloatCol, QUIFOY, QUIMEN, QUIFAM
from core.systemsf import SystemSf, Prestation
import numpy as np
from numpy import maximum as max_, minimum as min_
from parametres.paramData import XmlReader, Tree2Object
import datetime
from Utils import Scenario

date = datetime.date(2010,01,01)
reader = XmlReader('data/param.xml', date)
P = Tree2Object(reader.tree)

f = 'castypes/2010 - Couple - 1smic - 0smic.ofct'
scenario = Scenario()
scenario.openFile(f)

CHEF = QUIFAM['chef']
PART = QUIFAM['part']

def RaRsa(sal):
    return sal

def BrRmi(rarsa, cho, rst, alr, rto, brrmi_pfam, _option = {'rarsa': [CHEF, PART]}):
    '''
    Base ressource du Rmi/Rsa
    '''
    return rarsa[CHEF] + rarsa[PART] + cho + rst + alr + rto + brrmi_pfam

def Rsa(age, rarsa, so, nbpar, nbenf, brrmi, _P, _option = {'age':[CHEF, PART], 
                                                            'rarsa': [CHEF, PART]}):
    P = _P.minim.rmi
    nbpRmi = nbpar + nbenf
    loca = (3 <= so)&(5 >= so)
    eligib = (age[0] >=25) |(age[PART] >=25)
    tx_rmi = 1 + ( nbpRmi >= 2 )*P.txp2 \
               + ( nbpRmi >= 3 )*P.txp3 \
               + ( nbpRmi >= 4 )*((nbpar==1)*P.txps + (nbpar!=1)*P.txp3) \
               + max_(nbpRmi -4,0)*P.txps 
    rsaSocle = 12*P.rmi*tx_rmi*eligib
    # calcul du forfait logement si le ménage touche des allocations logements
    # (FA.AL)
    FL = P.forfait_logement
    tx_fl = ((nbpRmi==1)*FL.taux1 +
             (nbpRmi==2)*FL.taux2 +
             (nbpRmi>=3)*FL.taux3 )
    forf_log = 12*loca*(tx_fl*P.rmi)
    # cacul du RSA

    RMI = max_(0, rsaSocle  - forf_log - brrmi)
    RSA = max_(0, rsaSocle + P.pente*(rarsa[CHEF] + rarsa[PART]) - forf_log - brrmi)
    rsa = (RSA>=P.rsa_nv)*RSA
    return rsa

class InputTable(DataTable):
    '''
    Socio-economic data
    Donnée d'entrée de la simulation à fournir à partir d'une enquète ou 
    à générer avec un générateur de cas type
    '''
    noi = IntCol()

    idmen   = IntCol() # 600001, 600002,
    idfoy   = IntCol() # idmen + noi du déclarant
    idfam   = IntCol() # idmen + noi du chef de famille

    quimen  = IntCol(QUIMEN)
    quifoy  = IntCol(QUIFOY)
    quifam  = IntCol(QUIFAM)

    so = IntCol(default = 3)
    hsup = IntCol()
    inv = BoolCol()
    alt = BoolCol()
    choCheckBox = BoolCol()
    ppeCheckBox = BoolCol()
    agem = IntCol()
    zone_apl = IntCol()

    sal = FloatCol()
    cho = FloatCol()
    rst = FloatCol()
    rto = FloatCol()
    alr = FloatCol()
    brrmi_pfam = IntCol()
    loyer = IntCol()
    age = IntCol()
    activite = IntCol()
    statmarit = IntCol()
    ppeHeure = IntCol()
    
    nbpar = IntCol(default = 2)
    nbenf = IntCol(default = 1)

inputs = InputTable(101)
inputs.populate_from_scenario(scenario, date)
inputs.gen_index(['men', 'foy', 'fam'])

class France2010(SystemSf):
    rarsa  = Prestation(RaRsa, label = u"Revenu d'activité du rsa")
    brrmi  = Prestation(BrRmi, 'fam', label = u'Base ressource du rmi')
    rsa    = Prestation(Rsa, 'fam', label = u"Calcul du Rsa")
    
sys = France2010(P)
sys.set_inputs(inputs)
sys.calculate('rsa')

print sys.rsa.get_value()

