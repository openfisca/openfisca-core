# -*- coding: utf-8 -*-

import datetime

import numpy as np
from numpy.core.defchararray import startswith

from openfisca_core.formulas import dated_function, set_input_divide_by_period, calculate_output_add
from openfisca_core.entities import ADD, DIVIDE
from openfisca_core.columns import BoolCol, DateCol, FixedStrCol, FloatCol, IntCol
from openfisca_core.periods import MONTH, YEAR, ETERNITY
from openfisca_core.variables import Variable, DatedVariable

from openfisca_core.tests.dummy_country.entities import Famille, Individu


class af(Variable):
    column = FloatCol
    entity = Famille
    definition_period = MONTH
    set_input = set_input_divide_by_period


class age_en_mois(Variable):
    column = IntCol
    entity = Individu
    label = u"Âge (en nombre de mois)"
    definition_period = MONTH


class birth(Variable):
    column = DateCol
    entity = Individu
    label = u"Date de naissance"
    definition_period = ETERNITY


class depcom(Variable):
    column = FixedStrCol(max_length = 5)
    entity = Famille
    label = u"""Code INSEE "depcom" de la commune de résidence de la famille"""
    definition_period = ETERNITY


class salaire_brut(Variable):
    column = FloatCol
    entity = Individu
    label = "Salaire brut"
    definition_period = MONTH
    set_input = set_input_divide_by_period


class a_charge_fiscale(Variable):
    column = BoolCol
    entity = Individu
    label = u"La personne n'est pas fiscalement indépendante"
    definition_period = MONTH


# Calculated variables

class age(Variable):
    column = IntCol
    entity = Individu
    label = u"Âge (en nombre d'années)"
    definition_period = MONTH

    def function(self, simulation, period):
        birth = simulation.get_array('birth', period)
        if birth is None:
            age_en_mois = simulation.get_array('age_en_mois', period)
            if age_en_mois is not None:
                return age_en_mois // 12
            birth = simulation.calculate('birth', period)
        return (np.datetime64(period.date) - birth).astype('timedelta64[Y]')


class dom_tom(Variable):
    column = BoolCol
    entity = Famille
    label = u"La famille habite-t-elle les DOM-TOM ?"
    definition_period = YEAR

    def function(famille, period):
        depcom = famille('depcom', period)

        return np.logical_or(startswith(depcom, '97'), startswith(depcom, '98'))


class revenu_disponible(Variable):
    column = FloatCol
    entity = Individu
    label = u"Revenu disponible de l'individu"
    definition_period = YEAR

    def function(individu, period, legislation):
        rsa = individu('rsa', period, options = [ADD])
        salaire_imposable = individu('salaire_imposable', period)
        taux = legislation(period).impot.taux

        return rsa + salaire_imposable * (1 - taux)


class revenu_disponible_famille(Variable):
    column = FloatCol
    entity = Famille
    label = u"Revenu disponible de la famille"
    definition_period = YEAR

    def function(famille, period):
        revenu_disponible = famille.members('revenu_disponible', period)
        return famille.sum(revenu_disponible)


class rsa(DatedVariable):
    column = FloatCol
    entity = Individu
    label = u"RSA"
    definition_period = MONTH

    @dated_function(datetime.date(2010, 1, 1))
    def function_2010(individu, period):
        salaire_imposable = individu('salaire_imposable', period, options = [DIVIDE])

        return (salaire_imposable < 500) * 100.0

    @dated_function(datetime.date(2011, 1, 1), datetime.date(2012, 12, 31))
    def function_2011_2012(individu, period):
        salaire_imposable = individu('salaire_imposable', period, options = [DIVIDE])

        return (salaire_imposable < 500) * 200.0

    @dated_function(datetime.date(2013, 1, 1))
    def function_2013(individu, period):
        salaire_imposable = individu('salaire_imposable', period, options = [DIVIDE])

        return (salaire_imposable < 500) * 300


class salaire_imposable(Variable):
    column = FloatCol
    entity = Individu
    label = u"Salaire imposable"
    definition_period = YEAR

    def function(individu, period):
        dom_tom = individu.famille('dom_tom', period)

        salaire_net = individu('salaire_net', period, options=[ADD])

        return salaire_net * 0.9 - 100 * dom_tom


class salaire_net(Variable):
    column = FloatCol
    entity = Individu
    label = u"Salaire net"
    definition_period = MONTH
    set_input = set_input_divide_by_period
    calculate_output = calculate_output_add

    def function(individu, period):
        salaire_brut = individu('salaire_brut', period)

        return salaire_brut * 0.8


class csg(Variable):
    column = FloatCol
    entity = Individu
    label = u"CSG payées sur le salaire"
    definition_period = YEAR

    def function(individu, period, legislation):
        taux = legislation(period).csg.activite.deductible.taux
        salaire_brut = individu('salaire_brut', period, options=[ADD])

        return taux * salaire_brut
