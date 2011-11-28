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
    asf_elig = BoolCol(default=True)
    
    inactif  = BoolCol()
    partiel1 = BoolCol()
    partiel2 = BoolCol() 
    
    empl_dir = BoolCol() 
    ass_mat  = BoolCol() 
    gar_dom  = BoolCol()
    
    categ_inv = IntCol()
    
    
#   TODO REMOVEME testing only
    tspr  = FloatCol()
    rpns  = FloatCol()
    
    isol  = BoolCol(default=True)
    rev_coll = FloatCol()
    
    
inputs = InputTable(6)
inputs.populate_from_scenario(scenario, date)
inputs.gen_index(['men', 'foy', 'fam'])

from prestation.famille import (_biact, _tspr_fam, _rpns_fam, _rst_fam, _etu, _concub,
                                _af_nbenf, _af_base, _af_majo, _af_forf, _af,
                                _rev_pf, _br_pf, _cf, _asf, _ars,
                                _paje_base, _paje_nais, _paje_cumul_cf, _cf_cumul_paje,
                                _paje_clca, _paje_clca_taux_plein, _paje_clca_taux_partiel,
                                _paje_clmg,
                                _aeeh,
                                _ape, _apje
                                )

class Pfam(SystemSf):
    
    etu      = Prestation(_etu, label = u"Indicatrice individuelle étudiant")
    biact    = Prestation(_biact, 'fam', label = u"Indicatrice de biactivité")
    concub   = Prestation(_concub, 'fam', label = u"Indicatrice de vie en couple") 
    
    
    rpns_fam = Prestation(_tspr_fam, 'fam', label = u"Traitements, salaires, pensions et rentes de la famille")
    tspr_fam = Prestation(_rpns_fam, 'fam', label = u"Revenus des personnes non salariés de la famille")
    rst_fam  = Prestation(_rst_fam, 'fam', label = u"Retraites au sens strict de la famille")
    
    af_nbenf = Prestation(_af_nbenf, 'fam', u"Nombre d'enfant au sens des AF")
    af_base  = Prestation(_af_base, 'fam', label ='Allocations familiales - Base')
    af_majo  = Prestation(_af_majo, 'fam', label ='Allocations familiales - Majoration pour age')
    af_forf  = Prestation(_af_forf, 'fam', label ='Allocations familiales - Forfait 20 ans')
    af       = Prestation(_af, 'fam', label = u"Allocations familiales")
    
    
    rev_pf   = Prestation(_rev_pf, 'fam', label ='Base ressource individuele des prestations familiales')
    br_pf    = Prestation(_br_pf, 'fam', label ='Base ressource des prestations familiales')
    cf_temp  = Prestation(_cf, 'fam', label = u"Complément familial avant d'éventuels cumuls")
    asf      = Prestation(_asf, 'fam', label = u"Allocation de soutien familial")
# TODO mensualisation âge    ars     = Prestation(ARS, 'fam', label = u"Allocation de rentrée scolaire")
    paje_base_temp = Prestation(_paje_base, 'fam', label = u"Allocation de base de la PAJE sans tenir compte d'éventuels cumuls")
    paje_base      = Prestation(_paje_cumul_cf, 'fam', label = u"Allocation de base de la PAJE")
    cf             = Prestation(_cf_cumul_paje, 'fam', label = u"Complément familial avant d'éventuels cumuls")
    paje_nais      = Prestation(_paje_nais, 'fam', label = u"Allocation de naissance de la PAJE")
    paje_clca      = Prestation(_paje_clca, 'fam', label = u"PAJE - Complément de libre choix d'activité")
    paje_clca_taux_plein      = Prestation(_paje_clca_taux_plein, 'fam', label = u"Indicatrice Clca taux plein")
    paje_clca_taux_partiel      = Prestation(_paje_clca_taux_partiel, 'fam', label = u"Indicatrice Clca taux partiel ")
    #paje_clmg        = Prestation(Paje_Clmg, 'fam', label = u"PAJE - Complément de libre choix du mode de garde")
    aeeh           = Prestation(_aeeh, 'fam', label = u"Allocation d'éducation de l'enfant handicapé")


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
pfam.calculate('paje_clca')
pfam.calculate('paje_clca_taux_plein')
pfam.calculate('paje_clca_taux_partiel')
#pfam.calculate('paje_clmg')
pfam.calculate('aeeh')

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
print pfam.paje_clca.get_value()
print pfam.paje_clca_taux_plein.get_value()
print pfam.paje_clca_taux_partiel.get_value()
#print pfam.paje_clmg.get_value()
print pfam.aeeh.get_value()