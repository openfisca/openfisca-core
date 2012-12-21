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

from core.description import ModelDescription
from core.columns import IntCol, EnumCol, BoolCol, AgesCol
from core.utils import Enum

QUIFOY = Enum(['vous', 'conj', 'pac1','pac2','pac3','pac4','pac5','pac6','pac7','pac8','pac9'])
#QUIFAM = Enum(['chef', 'part', 'enf1','enf2','enf3','enf4','enf5','enf6','enf7','enf8','enf9'])
QUIMEN = Enum(['pref', 'cref', 'enf1','enf2','enf3','enf4','enf5','enf6','enf7','enf8','enf9'])
CAT    = Enum(['rsna', 'rsa', 'rsaa', 'rtns', 'rtte', 're', 'rtfr', 'raic', 'cnrps_sal', 'cnrps_pen'])


class InputTable(ModelDescription):
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
#    quifam  = EnumCol(QUIFAM)
    

    type_sal = EnumCol(CAT, default=0)
    
    inv = BoolCol(label = u'invalide')
    
    

    jour_xyz = IntCol(default = 360)
    age = AgesCol(label = u"âge")
    agem = AgesCol(label = u"âge (en mois)")
    
    loyer = IntCol(unit='men') # Loyer mensuel
    activite = IntCol()
    boursier = BoolCol()
    code_postal = IntCol(unit='men')
    so = IntCol()
    
    statmarit = IntCol(default = 2)
    chef      = BoolCol()

    # bic Bénéfices industriels et commerciaux
    # régime réel
    bic_reel  = EnumCol()
    # 0: Néant 1: commerçant – 2: industriel – 3: prestataire de services - 4: artisan – 5: plus qu'une activité. Les personnes soumises au régime forfaitaire qui ont cédé le fond de commerce peuvent déclarer l’impôt annuel sur le revenu au titre des bénéfices industriels et commerciaux sur la base de la différence entre les recettes et les dépenses .
    # régime des sociétés de personnes
    bic_sp = BoolCol()

    cadre_legal = EnumCol()
    # Code : 1: exportation totale dans le cadre du CII- 2 : développement régional - 3: développement agricole – 4: parcs des activités économiques – 5 : exportation dans le cadre du droit commun– 99: autre cadre ( à préciser).

    bic_reel_res = IntCol()
    bic_forf_res = IntCol()
    bic_sp_res   = IntCol()

    decl_inves = EnumCol()
    # (2) Code : 1:API- 2: APIA –3: commissariat régional du développement agricole –4: ONT –5:autre structure ( à préciser)


    # bnc Bénéfices des professions non commerciales
    bnc_reel = BoolCol()
    bnc_forf = BoolCol()
    
    # beap Bénéfices de l'exploitation agricole et de pêche
    beap_reel = BoolCol()
    beap_rd   = BoolCol()
    beap_ms   = BoolCol()
    beap_sp   = BoolCol()
    
    # rfon Revenus fonciers 
    #  régime réel
    fon_reel_fisc = IntCol()
    
    #  régime fofaitaire bâti
    fon_forf_bati_rec = IntCol()
    fon_forf_bati_rel = IntCol()
    fon_forf_bati_fra = IntCol()
    fon_forf_bati_tax = IntCol()

    # régime forfaitaire non bâti
    fon_forf_nbat_rec = IntCol()
    fon_forf_nbat_dep = IntCol()
    fon_forf_nbat_tax = IntCol()
    
    #  part dans les bénéfices ou els pertes de sociétés de personnes et assimilées qui réalisent des revenus fonciers
    fon_sp   = IntCol()

    # Salaires et pensions
    
    sali = IntCol( label="Salaires imposables", default=0)
    sal_nat = IntCol( label="Avantages en nature assimilables à des salaires", default=0 )
    smig = BoolCol( label="Salarié percevant le SMIG ou le SMAG")
    pen = IntCol(label="Pensions et rentes viagères")
    pen_nat = IntCol( label="Avantages en nature assimilables à des pensions")
    
    
# rvcm Revenus de valeurs mobilières et de capitaux mobiliers
# A Revenus des valeurs mobilières et de capitaux mobiliers
    valm_nreg = IntCol( label="Revenus des valeurs mobilières autres que ceux régulièrement distribués")
    valm_jpres     = IntCol( label="Jetons de présence")
    valm_aut  = IntCol( label="Autres rémunérations assimilées")

# B Revenus de capitaux mobiliers
    capm_banq   = IntCol( label="Intérêts bruts des comptes spéciaux d’épargne ouverts auprès des banques")
    capm_cent   = IntCol( label="Intérêts bruts des comptes spéciaux d’épargne ouverts auprès de la CENT")
    capm_caut   = IntCol( label="Intérêts des créances et intérêts et rémunérations des cautionnements")
    capm_part   = IntCol( label="Intérêts des titres de participation")
    capm_oblig  = IntCol( label="Intérêts des emprunts obligataires")
    capm_caisse = IntCol( label="Intérêts des bons de caisse")
    capm_plfcc  = IntCol( label="Revenus des parts et de liquidation du fonds commun des créances")
    capm_epinv  = IntCol( label="Intérêts des comptes épargne pour l'investissement")
    capm_aut    = IntCol( label="Autres intérêts")


# AUtres revenus
    etr_sal     = IntCol( label="Salaires perçus à l'étranger") 
    etr_pen     = IntCol( label="Pensions perçues à l'étranger (non transférées)")
    etr_trans   = IntCol( label="Pensions perçues à l'étranger (transférées en Tunisie)")
    etr_aut     = IntCol( label="Autres revenus perçus à l'étranger")
# Revnus exonérés
# Revenus non imposables        
    
# deficit antérieurs non déduits
    def_ante    = IntCol( label="Déficits des années antérieures non déduits")   
    
# déductions 

# 1/ Au titre de l'activité
#    
#    Droit commun
#- Déduction de la plus value provenant de l’apport d’actions et de parts sociales au capital de la société mère ou de la société holding 6811
#- Déduction de la plus value provenant de la cession des entreprises en difficultés économiques dans le cadre de la transmission des entreprises 6881
#- Déduction de la plus value provenant de la cession des entreprises suite à l’atteinte du propriétaire de l’âge de la retraite ou à l’incapacité de poursuivre la gestion de l’entreprise dans le cadre de la transmission des entreprises. 6891
#- Déduction de la plus value provenant de l'intégration des éléments d'actifs. 6851
#- Déduction de la plus value provenant de la cession des actions cotées en bourse 6841
#- Bénéfices provenant des opérations de courtage international 1141
#- Exportation 1191
#- Location d’immeubles au profit des étudiants 1211 1212 1213
#- Bénéfices provenant des services de restauration au profit des étudiants, des élèves et des apprenants dans les centres de formation professionnelle de base. 1221 1222 1223
#- Bénéfices provenant de la location des constructions verticales destinées à l’habitat collectif social ou économique. 1251
#- Bénéfices provenant de l’exploitation des bureaux d’encadrement et d’assistance fiscale 1311
#- Bénéfices réinvestis dans le capital des sociétés qui commercialisent exclusivement des marchandises ou services tunisiens 1132
#- Bénéfices réinvestis dans les SICAR ou placés auprès d'elles dans des fonds de capital à risque ou dans des fonds de placement à risque qui se conforment aux exigences de l'article 21 de la loi n°: 88-92 relative au sociétés d'investissement. 6872
#- Bénéfices réinvestis dans les SICAR ou placés auprès d'elles dans des fonds de capital à risque ou dans des fonds de placement à risque qui utilisent 75% au moins de leur capital libéré et des montants mis à sa disposition et de leurs actifs dans le financement des projets implantés dans les zones de développement.
#6842
#- Revenus et bénéfices placés dans les fonds d’amorçage
#1432
#- Montants déposés dans les comptes épargne pour l’investissement dans la limite de 20000 D
#1412
#- Montants déposés dans les comptes épargne en actions dans la limite de 20000 D
#1422
#- Bénéfices réinvestis pour l’acquisition d’entreprises ou de titres cédés suite à l’atteinte du propriétaire de l’âge de la retraite ou à son incapacité de poursuivre la gestion de l’entreprise
#1512
#- Bénéfices réinvestis pour l’acquisition d’entreprises cédées dans le cadre de cession d’entreprises en difficultés économiques dans le cadre de la loi n° 34 de l'année 1995.
#1522

#     2/ Autres déductions
    
    deduc_banq  = IntCol( label="Intérêts des comptes spéciaux d’épargne ouverts auprès des banques")
    deduc_cent  = IntCol( label="Intérêts des comptes spéciaux d’épargne ouverts auprès de la CENT dans la limite")
    deduc_obli  = IntCol( label="Intérêts des emprunts obligataires")
    deduc_epinv = IntCol( label="Intérêts des comptes épargne pour l'investissement")
    rente       = IntCol( label="Rentes payées obligatoirement et à titre gratuit")
    prime_ass_vie     = IntCol( label="Prime d’assurance-vie")
    dons        = IntCol( label="Dons au profit du fonds national de solidarité 26-26 et du Fonds National de l’Emploi 21-21")
    pret_univ   = IntCol( label="Remboursement des prêts universitaires en principal et intérêts")
    cotis_nonaf = IntCol( label="Les cotisations payées par les travailleurs non salariés affiliés à l’un des régimes légaux de la sécurité sociale")
    deduc_logt  = IntCol( label="Les intérêts payés au titre des prêts relatifs à l’acquisition ou à la construction d’un logement social")
    

#Code d’incitation aux investissements
#Incitations Communes 3::3
#Bénéfices réinvestis dans l'acquisition des éléments d'actif d'une société ou dans l'acquisition ou la souscription d'actions ou de parts permettant de posséder 50% au moins du capital d'une société 2982
#Déduction de 20% des revenus et bénéfices soumis à l'impôt sur le revenu de la part des entreprises dont le chiffre d’affaires annuel ne dépasse pas 150 milles dinars pour les activités de services et 300 milles dinars pour les autres activités sans dépasser un chiffre d’affaires annuel de 300 milles dinars qui confient la tenue de leurs comptes et la préparation de leurs déclarations fiscales aux centres de gestion intégrés. (1) 2971
#Exportation totale (pendant la période de la déduction totale). 3222 3223
#Investissement au capital des sociétés de commerce international totalement exportateur. 2172
#Déduction des bénéfices provenant de la gestion d'une zone portuaire destinée au tourisme de croisière (pendant les dix premières années à partir de la date d'entrée en activité effective) 2151
#Déduction des bénéfices provenant de la gestion d'une zone portuaire destinée au tourisme de croisière (à partir de la onzième année de la date d'entrée en activité effective) 2161
#Déduction des bénéfices réinvestis dans l'acquisition des éléments d'actif d'une société totalement exportatrice ou dans l'acquisition d'actions ou de parts permettant de posséder 50% au moins du capital d'une société totalement exportatrice dans le cadre de la loi n° 34 de l'année 1995. 2142
#Exportation partielle. 3232
#Développement régional: le premier groupe 3461 3463
#Développement régional: le deuxième groupe 2371 2372
#Développement régional prioritaire pendant les dix premières années à partir de la date d'entrée en activité effective ( 2) 2391 2392
#Développement régional prioritaire pendant les dix années qui suivent des dix premières années à partir de la date d'entrée en activité effective ( 2) 2381 2382
#Déduction des bénéfices réinvestis dans l'acquisition des éléments d'actif des sociétés exerçant dans les zones d'encouragement au développement régional ou dans l'acquisition ou la souscription d'actions ou de parts permettant de posséder 50% au moins du capital de ces sociétés dans le cadre de la loi n° 34 de l'année 1995. 2352
#Travaux publics et promotion immobilière dans la zone de développement régional . 3422
#Développement agricole 35:2 35:3
#Investissements agricoles réalisés dans les régions à climat difficile ainsi que les investissements de pêche dans les zones insuffisamment exploitées 3523
#Lutte contre la pollution 38:2 38:3
#Activités de soutien 33:2 33:3
#Bénéfices provenant de projets réalisés par les promoteurs immobiliers concernant les programmes de logements sociaux et de réaménagement des zones d’activités agricoles, touristiques, industrielles et les bâtiments pour les activités industrielles.
#36:2
#Sociétés implantées dans les parcs des activités économiques
#4262 4263
#Bénéfices et revenus réinvestis dans le cadre de la mise à niveau des entreprises publiques.
#    
    

    # TODO Remove Me
    rstbrut  = IntCol()
    alr = IntCol()
    alv = IntCol()
    rto = IntCol()
    psoc = IntCol()
    af = IntCol()
    uc = IntCol()