# -*- coding:utf-8 -*-Boll
# Copyright © 2012 Clément Schaff, Mahdi Ben Jelloul

"""
openFiscaTn, Logiciel libre de simulation du système socio-fiscal tunisien
Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

This file is part of openFiscaTn.

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

from datetime import date
from core.description import ModelDescription
from core.columns import Prestation, BoolPresta
import tunisia.model.cotsoc as cs
import tunisia.model.irpp as ir
import tunisia.model.common as cm
import tunisia.model.pfam as pf


class ModelSF(ModelDescription):
    

    ############################################################
    # Cotisations sociales
    ############################################################
    
    # Salaires
    salbrut = Prestation(cs._salbrut, label="Salaires bruts")
    cotpat  = Prestation(cs._cotpat)
    cotsal  = Prestation(cs._cotsal)
    salsuperbrut = Prestation(cs._salsuperbrut, label="Salaires super bruts")
#    sal = Prestation(cs._sal)        
    

    # Pension
    
    ############################################################
    # Prestation familiales
    ############################################################
    
    smig75   = BoolPresta(pf._smig75, label="Indicatrice de salaire supérieur à 75% du smig" ) 
    af_nbenf = Prestation(pf._af_nbenf, 'foy', label="Nombre d'enfants au sens des allocations familiales")
    af  = Prestation(pf._af, 'foy', label="Allocations familiales")
    sal_uniq = BoolPresta(pf._sal_uniq, 'foy', label="Indicatrice de salaire unique")
    maj_sal_uniq = Prestation(pf._maj_sal_uniq, 'foy', label="Majoration du salaire unique")
    contr_creche = Prestation(pf._contr_creche, 'foy', label="Contribution aux frais de crêche")
    pfam = Prestation(pf._pfam, 'foy', label="Prestations familales")
    
    ############################################################
    # Impôt sur le revenu
    ############################################################

    marie = BoolPresta(ir._marie, 'foy')
    celdiv = BoolPresta(ir._celib, 'foy')
    divor = BoolPresta(ir._divor, 'foy')
    veuf = BoolPresta(ir._veuf, 'foy')
    
    nb_enf = Prestation(ir._nb_enf, 'foy')
    nb_enf_sup = Prestation(ir._nb_enf_sup, 'foy')
    nb_par     = Prestation(ir._nb_par, 'foy')
    nb_infirme = Prestation(ir._nb_infirme, 'foy')
    
#    rbg = Prestation(ir._rbg, 'foy', label = u"Revenu brut global")
    
    bic = Prestation(ir._bic, 'foy')
    bnc = Prestation(ir._bnc, 'foy')
    beap = Prestation(ir._beap, 'foy')
    rvcm = Prestation(ir._rvcm, 'foy')
    fon_forf_bati = Prestation(ir._fon_forf_bati, 'foy')
    fon_forf_nbat = Prestation(ir._fon_forf_nbat, 'foy')
    rfon = Prestation(ir._rfon, 'foy')

    sal = Prestation(ir._sal, 'foy', "Salaires y compris salaires en nature")
    sal_net = Prestation(ir._sal_net, 'foy', "Salaires nets")
    pen_net = Prestation(ir._pen_net, 'foy')                               
    tspr    = Prestation(ir._tspr, 'foy')
    retr    = Prestation(ir._retr, 'foy')
    rng = Prestation(ir._rng, 'foy', label = u"Revenu net global")
    
    # Déductions
    
    deduc_fam = Prestation(ir._deduc_fam, 'foy', label = u"Déductions pour situation et charges de famille")
    deduc_rente     = Prestation(ir._deduc_rente, 'foy', label = u"Arrérages et rentes payées à titre obligatoire et gratuit")
    ass_vie   = Prestation(ir._ass_vie, 'foy', label = u"Primes afférentes aux contrats d'assurance-vie")
    # réductions d'impots
    
    deduc_smig = Prestation(ir._deduc_smig, 'foy', label = u"Déduction supplémentaire pour les salariés payés au SMIG et SMAG")
    rni = Prestation(ir._rni, 'foy', label = u"Revenu net imposable")
    ir_brut = Prestation(ir._ir_brut, 'foy', label = u"Impôt avant non-imposabilité")
    irpp = Prestation(ir._irpp, 'foy', label = u"Impôt sur le revenu des personnes physiques")

    ############################################################
    # Unité de consommation du ménage
    ############################################################
#    uc = Prestation(cm._uc, 'men', label = u"Unités de consommation")

#    ############################################################
#    # Catégories
#    ############################################################
#    
#    typ_men = IntPresta(cm._typ_men, 'men', label = u"Type de ménage")
#    nb_ageq0 = IntPresta(cl._nb_ageq0, 'men', label = u"Effectifs des tranches d'âge quiquennal")
#    nbinde2 = IntPresta(cl._nbinde2, 'men', label = u"Nombre d'individus dans le ménage")
#
    ############################################################
    # Totaux
    ############################################################

    revdisp_i = Prestation(cm._revdisp_i, label = u"Revenu disponible individuel")
    revdisp = Prestation(cm._revdisp, 'men', label = u"Revenu disponible du ménage")
    nivvie = Prestation(cm._nivvie, 'men', label = u"Niveau de vie du ménage")
    rev_trav = Prestation(cm._rev_trav)
#    pen = Prestation(cm._pen)
#    
#    rstnet = Prestation(cm._rstnet)
    rev_cap = Prestation(cm._rev_cap)
#    
    
    impo = Prestation(cm._impo)

