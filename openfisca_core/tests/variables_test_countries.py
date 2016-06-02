# -*- coding: utf-8 -*-

import datetime

import numpy as np
from numpy.core.defchararray import startswith

from openfisca_core.columns import BoolCol, DateCol, FixedStrCol, FloatCol, IntCol
from openfisca_core.formulas import (dated_function, DatedVariable, EntityToPersonColumn,
    PersonToEntityColumn, set_input_divide_by_period, Variable)
from openfisca_core.tests.dummy_country import Familles, Individus
from openfisca_core.variables import NewVariable, NewEntityToPersonColumn


# Input variables

class age_en_mois(NewVariable):
    column = IntCol
    entity_class = Individus
    label = u"Âge (en nombre de mois)"


class birth(NewVariable):
    column = DateCol
    entity_class = Individus
    label = u"Date de naissance"


class depcom(NewVariable):
    column = FixedStrCol(max_length = 5)
    entity_class = Familles
    is_permanent = True
    label = u"""Code INSEE "depcom" de la commune de résidence de la famille"""


class salaire_brut(NewVariable):
    column = FloatCol
    entity_class = Individus
    label = "Salaire brut"
    set_input = set_input_divide_by_period


# Calculated variables

class age(Variable):
    column = IntCol
    entity_class = Individus
    label = u"Âge (en nombre d'années)"

    def function(self, simulation, period):
        birth = simulation.get_array('birth', period)
        if birth is None:
            age_en_mois = simulation.get_array('age_en_mois', period)
            if age_en_mois is not None:
                return period, age_en_mois // 12
            birth = simulation.calculate('birth', period)
        return period, (np.datetime64(period.date) - birth).astype('timedelta64[Y]')


class dom_tom(Variable):
    column = BoolCol
    entity_class = Familles
    label = u"La famille habite-t-elle les DOM-TOM ?"

    def function(self, simulation, period):
        period = period.start.period(u'year').offset('first-of')
        depcom = simulation.calculate('depcom', period)

        return period, np.logical_or(startswith(depcom, '97'), startswith(depcom, '98'))


class dom_tom_individu(NewEntityToPersonColumn):
    entity_class = Individus
    label = u"La personne habite-t-elle les DOM-TOM ?"
    variable = "dom_tom"


class revenu_disponible(Variable):
    column = FloatCol
    entity_class = Individus
    label = u"Revenu disponible de l'individu"

    def function(self, simulation, period):
        period = period.start.period(u'year').offset('first-of')
        rsa = simulation.calculate_add('rsa', period)
        salaire_imposable = simulation.calculate('salaire_imposable', period)

        return period, rsa + salaire_imposable * 0.7


class revenu_disponible_famille(PersonToEntityColumn):
    entity_class = Familles
    label = u"Revenu disponible de la famille"
    operation = 'add'
    variable = revenu_disponible


class rsa(DatedVariable):
    column = FloatCol
    entity_class = Individus
    label = u"RSA"

    @dated_function(datetime.date(2010, 1, 1))
    def function_2010(self, simulation, period):
        period = period.start.period(u'month').offset('first-of')
        salaire_imposable = simulation.calculate_divide('salaire_imposable', period)

        return period, (salaire_imposable < 500) * 100.0

    @dated_function(datetime.date(2011, 1, 1), datetime.date(2012, 12, 31))
    def function_2011_2012(self, simulation, period):
        period = period.start.period(u'month').offset('first-of')
        salaire_imposable = simulation.calculate_divide('salaire_imposable', period)

        return period, (salaire_imposable < 500) * 200.0

    @dated_function(datetime.date(2013, 1, 1))
    def function_2013(self, simulation, period):
        period = period.start.period(u'month').offset('first-of')
        salaire_imposable = simulation.calculate_divide('salaire_imposable', period)

        return period, (salaire_imposable < 500) * 300


class salaire_imposable(Variable):
    column = FloatCol
    entity_class = Individus
    label = u"Salaire imposable"

    def function(self, simulation, period):
        period = period.start.period(u'year').offset('first-of')
        dom_tom_individu = simulation.calculate('dom_tom_individu', period)
        salaire_net = simulation.calculate('salaire_net', period)

        return period, salaire_net * 0.9 - 100 * dom_tom_individu


class salaire_net(Variable):
    column = FloatCol
    entity_class = Individus
    label = u"Salaire net"

    def function(self, simulation, period):
        period = period.start.period(u'year').offset('first-of')
        salaire_brut = simulation.calculate('salaire_brut', period)

        return period, salaire_brut * 0.8
