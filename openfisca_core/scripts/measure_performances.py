#! /usr/bin/env python
# -*- coding: utf-8 -*-


"""Measure performances of a basic tax-benefit system to compare to other OpenFisca implementations."""


import argparse
import collections
import datetime
import logging
import sys
import time

import numpy as np
from numpy.core.defchararray import startswith

from openfisca_core import periods, simulations
from openfisca_core.columns import BoolCol, DateCol, FixedStrCol, FloatCol, IntCol
from openfisca_core.entities import AbstractEntity
from openfisca_core.formulas import (
    dated_function,
    DatedVariable,
    EntityToPersonColumn,
    PersonToEntityColumn,
    Variable,
    )
from openfisca_core.taxbenefitsystems import AbstractTaxBenefitSystem
from openfisca_core.tools import assert_near


args = None


def timeit(method):
    def timed(*args, **kwargs):
        start_time = time.time()
        result = method(*args, **kwargs)
        # print '%r (%r, %r) %2.9f s' % (method.__name__, args, kw, time.time() - start_time)
        print '{:2.6f} s'.format(time.time() - start_time)
        return result

    return timed


# Entities


PARENT1 = 0
PARENT2 = 1


class Familles(AbstractEntity):
    column_by_name = collections.OrderedDict()
    index_for_person_variable_name = 'id_famille'
    key_plural = 'familles'
    key_singular = 'famille'
    label = u'Famille'
    max_cardinality_by_role_key = {'parents': 2}
    role_for_person_variable_name = 'role_dans_famille'
    roles_key = ['parents', 'enfants']
    label_by_role_key = {
        'enfants': u'Enfants',
        'parents': u'Parents',
        }
    symbol = 'fam'


class Individus(AbstractEntity):
    column_by_name = collections.OrderedDict()
    is_persons_entity = True
    key_plural = 'individus'
    key_singular = 'individu'
    label = u'Personne'
    symbol = 'ind'


entity_class_by_symbol = dict(
    fam = Familles,
    ind = Individus,
    )


# TaxBenefitSystems


def init_country():
    class TaxBenefitSystem(AbstractTaxBenefitSystem):
        entity_class_by_key_plural = {
            entity_class.key_plural: entity_class
            for entity_class in entity_class_by_symbol.itervalues()
            }

    return TaxBenefitSystem


# Input variables


class age_en_mois(Variable):
    column = IntCol
    entity_class = Individus
    label = u"Âge (en nombre de mois)"


class birth(Variable):
    column = DateCol
    entity_class = Individus
    label = u"Date de naissance"


class depcom(Variable):
    column = FixedStrCol(max_length = 5)
    entity_class = Familles
    is_permanent = True
    label = u"""Code INSEE "depcom" de la commune de résidence de la famille"""


class id_famille(Variable):
    column = IntCol
    entity_class = Individus
    is_permanent = True
    label = u"Identifiant de la famille"


class role_dans_famille(Variable):
    column = IntCol
    entity_class = Individus
    is_permanent = True
    label = u"Rôle dans la famille"


class salaire_brut(Variable):
    column = FloatCol
    entity_class = Individus
    label = "Salaire brut"


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
        period = period.start.period('year').offset('first-of')
        depcom = simulation.calculate('depcom', period)
        return period, np.logical_or(startswith(depcom, '97'), startswith(depcom, '98'))


class dom_tom_individu(EntityToPersonColumn):
    entity_class = Individus
    label = u"La personne habite-t-elle les DOM-TOM ?"
    variable = dom_tom


class revenu_disponible(Variable):
    column = FloatCol
    entity_class = Individus
    label = u"Revenu disponible de l'individu"

    def function(self, simulation, period):
        period = period.start.period(u'year').offset('first-of')
        rsa = simulation.calculate('rsa', period)
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
        salaire_imposable = simulation.calculate('salaire_imposable', period)
        return period, (salaire_imposable < 500) * 100.0

    @dated_function(datetime.date(2011, 1, 1), datetime.date(2012, 12, 31))
    def function_2011_2012(self, simulation, period):
        period = period.start.period(u'month').offset('first-of')
        salaire_imposable = simulation.calculate('salaire_imposable', period)
        return period, (salaire_imposable < 500) * 200.0

    @dated_function(datetime.date(2013, 1, 1))
    def function_2013(self, simulation, period):
        period = period.start.period(u'month').offset('first-of')
        salaire_imposable = simulation.calculate('salaire_imposable', period)
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


# TaxBenefitSystem instance declared after formulas


TaxBenefitSystem = init_country()
tax_benefit_system = TaxBenefitSystem()


@timeit
def check_revenu_disponible(year, depcom, expected_revenu_disponible):
    simulation = simulations.Simulation(period = periods.period(year), tax_benefit_system = tax_benefit_system)
    famille = simulation.entity_by_key_singular["famille"]
    famille.count = 3
    famille.roles_count = 2
    famille.step_size = 1
    individu = simulation.entity_by_key_singular["individu"]
    individu.count = 6
    individu.step_size = 2
    simulation.get_or_new_holder("depcom").array = np.array([depcom, depcom, depcom])
    simulation.get_or_new_holder("id_famille").array = np.array([0, 0, 1, 1, 2, 2])
    simulation.get_or_new_holder("role_dans_famille").array = np.array([PARENT1, PARENT2, PARENT1, PARENT2, PARENT1,
        PARENT2])
    simulation.get_or_new_holder("salaire_brut").array = np.array([0.0, 0.0, 50000.0, 0.0, 100000.0, 0.0])
    revenu_disponible = simulation.calculate('revenu_disponible')
    assert_near(revenu_disponible, expected_revenu_disponible, absolute_error_margin = 0.005)
    # revenu_disponible_famille = simulation.calculate('revenu_disponible_famille')
    # expected_revenu_disponible_famille = np.array([
    #     expected_revenu_disponible[i] + expected_revenu_disponible[i + 1]
    #     for i in range(0, len(expected_revenu_disponible), 2)
    #     ])
    # assert_near(revenu_disponible_famille, expected_revenu_disponible_famille, absolute_error_margin = 0.005)


def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = "increase output verbosity")
    global args
    args = parser.parse_args()
    logging.basicConfig(level = logging.DEBUG if args.verbose else logging.WARNING, stream = sys.stdout)

    check_revenu_disponible(2009, '75101', np.array([0, 0, 25200, 0, 50400, 0]))
    check_revenu_disponible(2010, '75101', np.array([1200, 1200, 25200, 1200, 50400, 1200]))
    check_revenu_disponible(2011, '75101', np.array([2400, 2400, 25200, 2400, 50400, 2400]))
    check_revenu_disponible(2012, '75101', np.array([2400, 2400, 25200, 2400, 50400, 2400]))
    check_revenu_disponible(2013, '75101', np.array([3600, 3600, 25200, 3600, 50400, 3600]))

    check_revenu_disponible(2009, '97123', np.array([-70.0, -70.0, 25130.0, -70.0, 50330.0, -70.0]))
    check_revenu_disponible(2010, '97123', np.array([1130.0, 1130.0, 25130.0, 1130.0, 50330.0, 1130.0]))
    check_revenu_disponible(2011, '98456', np.array([2330.0, 2330.0, 25130.0, 2330.0, 50330.0, 2330.0]))
    check_revenu_disponible(2012, '98456', np.array([2330.0, 2330.0, 25130.0, 2330.0, 50330.0, 2330.0]))
    check_revenu_disponible(2013, '98456', np.array([3530.0, 3530.0, 25130.0, 3530.0, 50330.0, 3530.0]))


if __name__ == "__main__":
    sys.exit(main())
