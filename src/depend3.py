# -*- coding: utf-8 -*-
from __future__ import division
from core.datatable import DataTable, AgesCol, IntCol, BoolCol, FloatCol, EnumCol, QUIFOY, QUIMEN, QUIFAM
from core.systemsf import SystemSf, Prestation
from parametres.paramData import XmlReader, Tree2Object
import datetime
from Utils import Scenario

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
    brrmi_pfam = IntCol()#
    loyer = IntCol()
    age = AgesCol()#
    activite = IntCol()
    statmarit = IntCol()
    ppeHeure = IntCol()
    
    nbpar = IntCol(default = 2)
    asf_elig = BoolCol(default=True)
    
#   TODO REMOVEME testing only
    tspr  = FloatCol()
    rpns  = FloatCol()
    
    isol  = BoolCol(default=True)
    rev_coll = FloatCol()
    
inputs = InputTable(6)
inputs.populate_from_scenario(scenario, date)
inputs.gen_index(['men', 'foy', 'fam'])

from prestation.famille import (AF_NbEnf, AF_Base, AF_Majo, AF_Forf, AF, 
                                Biact, Tspr_Fam, Rpns_Fam, 
                                Rev_PF, Br_PF, CF, ASF, ARS,
                                Paje_Base, Paje_Nais, Paje_CumulCf, Cf_CumulPaje)

class Pfam(SystemSf):
    
    biact    = Prestation(Biact, 'fam', label = u"Indicatrice de biactivité")
    rpns_fam = Prestation(Tspr_Fam, 'fam', label = u"Traitements, salaires, pensions et rentes de la famille")
    tspr_fam = Prestation(Rpns_Fam, 'fam', label = u"Revenus des personnes non salariés de la famille")
    rst_fam  = Prestation(Rpns_Fam, 'fam', label = u"Retraites au sens strict de la famille")
    
    af_nbenf = Prestation(AF_NbEnf, 'fam', u"Nombre d'enfant au sens des AF")
    af_base  = Prestation(AF_Base, 'fam', label ='Allocations familiales - Base')
    af_majo  = Prestation(AF_Majo, 'fam', label ='Allocations familiales - Majoration pour age')
    af_forf  = Prestation(AF_Forf, 'fam', label ='Allocations familiales - Forfait 20 ans')
    af       = Prestation(AF, 'fam', label = u"Allocations familiales")
    
    
    rev_pf   = Prestation(Rev_PF, 'fam', label ='Base ressource individuele des prestations familiales')
    br_pf    = Prestation(Br_PF, 'fam', label ='Base ressource des prestations familiales')
    cf_temp  = Prestation(CF, 'fam', label = u"Complément familial avant d'éventuels cumuls")
    asf      = Prestation(ASF, 'fam', label = u"Allocation de soutien familial")
# TODO mensualisation âge    ars     = Prestation(ARS, 'fam', label = u"Allocation de rentrée scolaire")
    paje_base_temp = Prestation(Paje_Base, 'fam', label = u"Allocation de base de la PAJE sans tenir compte d'éventuels cumuls")
    paje_base      = Prestation(Paje_CumulCf, 'fam', label = u"Allocation de base de la PAJE")
    cf             = Prestation(Cf_CumulPaje, 'fam', label = u"Complément familial avant d'éventuels cumuls")
    paje_nais      = Prestation(Paje_Nais, 'fam', label = u"Allocation de naissance de la PAJE")

pfam = Pfam(P)
pfam.set_inputs(inputs)
pfam.calculate('af')
pfam.calculate('cf_temp')
pfam.calculate('asf')
#pfam.calculate('ars')
pfam.calculate('paje_base_temp')
pfam.calculate('cf')
pfam.calculate('paje_base')
pfam.calculate('paje_nais')

print inputs.age.get_value()
print pfam.af.get_value()
print pfam.af_nbenf.get_value()
print pfam.af_base.get_value()

print pfam.cf_temp.get_value()
print pfam.cf.get_value()
print pfam.asf.get_value()
#print pfam.ars.get_value()
print pfam.paje_base.get_value()
print pfam.paje_nais.get_value()
