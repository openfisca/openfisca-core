# -*- coding: utf-8 -*-
from __future__ import division
from core.datatable import DataTable, AgesCol, IntCol, BoolCol, FloatCol, EnumCol, DateCol
from core.systemsf import SystemSf, Prestation
from core.utils import Enum
from parametres.paramData import XmlReader, Tree2Object
import datetime
from Utils import Scenario


QUIFOY = Enum(['vous', 'conj', 'pac1','pac2','pac3','pac4','pac5','pac6','pac7','pac8','pac9'])
QUIFAM = Enum(['chef', 'part', 'enf1','enf2','enf3','enf4','enf5','enf6','enf7','enf8','enf9'])
QUIMEN = Enum(['pref', 'cref', 'enf1','enf2','enf3','enf4','enf5','enf6','enf7','enf8','enf9'])
CAT    = Enum(['noncadre', 'cadre', 'fonc'])


date = datetime.date(2010,01,01)
reader = XmlReader('data/param.xml', date)
P = Tree2Object(reader.tree)

f = 'castypes/2010 - Couple 3 enfants.ofct'
scenario = Scenario()
scenario.openFile(f)

class InputTable(DataTable):
    '''
    Socio-economic data
    Donnée d'entrée de la simulation à fournir à partir d'une enquète ou 
    à générer avec un générateur de cas type
    '''
    noi = IntCol()
    birth = DateCol()

    idmen   = IntCol() # 600001, 600002,
    idfoy   = IntCol() # idmen + noi du déclarant
    idfam   = IntCol() # idmen + noi du chef de famille

    quimen  = EnumCol(QUIMEN)
    quifoy  = EnumCol(QUIFOY)
    quifam  = EnumCol(QUIFAM)

    so = IntCol(default = 3)#
    hsup = IntCol()
    inv = BoolCol()
    alt = BoolCol()
    choCheckBox = BoolCol()
    ppeCheckBox = BoolCol()
    agem = IntCol()
    zone_apl = IntCol()

    sal = FloatCol()#
    cho = FloatCol()#
    rst = FloatCol()#
    rto = FloatCol()#
    alr = FloatCol()#
    fra = FloatCol()
    statmarit = FloatCol()
    
    brrmi_pfam = IntCol()#
    loyer = IntCol()
    age = AgesCol()#
    activite = IntCol()
    statmarit = IntCol()
    ppeHeure = IntCol()
    
    nbpar = IntCol(default = 2)

inputs = InputTable(6)
inputs.populate_from_scenario(scenario, date)
inputs.gen_index(['men', 'foy', 'fam'])

from prestation.famille import AF_NbEnf, AF_Base, AF_Majo, AF_Forf, AF

class Pfam(SystemSf):
    af_nbenf = Prestation(AF_NbEnf, 'fam', u"Nombre d'enfant au sens des AF")
    af_base = Prestation(AF_Base, 'fam', 'Allocations familiales - Base')
    af_majo = Prestation(AF_Majo, 'fam', 'Allocations familiales - Majoration pour age')
    af_forf = Prestation(AF_Forf, 'fam', 'Allocations familiales - Forfait 20 ans')
    af      = Prestation(AF, 'fam', label = u"Allocations familiales")

#    rev_pf  = Prestation(Rev_PF, 'Base ressource individuele des prestations familiales')
#    br_pf   = Prestation(Br_PF, 'fam', 'Base ressource des prestations familiales')
#    cf      = Prestation(CF, 'fam', label = u"Complément familiale")

pfam = Pfam(P)
pfam.set_inputs(inputs)
pfam.calculate('af')
print inputs.age.get_value()
print pfam.af.get_value()
print pfam.af_nbenf.get_value()
print pfam.af_base.get_value()
