# -*- coding: utf-8 -*-

import datetime

import numpy as np
from numpy.core.defchararray import startswith
from nose.tools import raises

from openfisca_core.columns import BoolCol, DateCol, FixedStrCol, FloatCol, IntCol
from openfisca_core.formulas import dated_function, set_input_divide_by_period
from openfisca_core.variables import Variable, DatedVariable
from openfisca_core.taxbenefitsystems import VariableNameConflict, VariableNotFound
from openfisca_core import periods
from openfisca_core.entities import ADD, DIVIDE
from dummy_country import Famille, Individu, DummyTaxBenefitSystem
from openfisca_core.tools import assert_near

# Input variables


class af(Variable):
    column = FloatCol
    entity = Famille


class age_en_mois(Variable):
    column = IntCol
    entity = Individu
    label = u"Âge (en nombre de mois)"


class birth(Variable):
    column = DateCol
    entity = Individu
    label = u"Date de naissance"


class depcom(Variable):
    column = FixedStrCol(max_length = 5)
    entity = Famille
    is_permanent = True
    label = u"""Code INSEE "depcom" de la commune de résidence de la famille"""


class salaire_brut(Variable):
    column = FloatCol
    entity = Individu
    label = "Salaire brut"
    set_input = set_input_divide_by_period


# Calculated variables

class age(Variable):
    column = IntCol
    entity = Individu
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
    entity = Famille
    label = u"La famille habite-t-elle les DOM-TOM ?"

    def function(famille, period):
        period = period.start.period(u'year').offset('first-of')

        depcom = famille('depcom', period)

        return period, np.logical_or(startswith(depcom, '97'), startswith(depcom, '98'))


class revenu_disponible(Variable):
    column = FloatCol
    entity = Individu
    label = u"Revenu disponible de l'individu"

    def function(individu, period, legislation):
        period = period.start.period(u'year').offset('first-of')
        rsa = individu('rsa', period, options = [ADD])
        salaire_imposable = individu('salaire_imposable', period)
        taux = legislation(period).impot.taux

        return period, rsa + salaire_imposable * (1 - taux)


class revenu_disponible_famille(Variable):
    column = FloatCol
    entity = Famille
    label = u"Revenu disponible de la famille"

    def function(famille, period):
        revenu_disponible = famille.members('revenu_disponible', period)
        return period, famille.sum(revenu_disponible)


class rsa(DatedVariable):
    column = FloatCol
    entity = Individu
    label = u"RSA"

    @dated_function(datetime.date(2010, 1, 1))
    def function_2010(individu, period):
        period = period.start.period(u'month').offset('first-of')
        salaire_imposable = individu('salaire_imposable', period, options = [DIVIDE])

        return period, (salaire_imposable < 500) * 100.0

    @dated_function(datetime.date(2011, 1, 1), datetime.date(2012, 12, 31))
    def function_2011_2012(individu, period):
        period = period.start.period(u'month').offset('first-of')
        salaire_imposable = individu('salaire_imposable', period, options = [DIVIDE])

        return period, (salaire_imposable < 500) * 200.0

    @dated_function(datetime.date(2013, 1, 1))
    def function_2013(individu, period):
        period = period.start.period(u'month').offset('first-of')
        salaire_imposable = individu('salaire_imposable', period, options = [DIVIDE])

        return period, (salaire_imposable < 500) * 300


class salaire_imposable(Variable):
    column = FloatCol
    entity = Individu
    label = u"Salaire imposable"

    def function(individu, period):
        period = period.start.period(u'year').offset('first-of')
        dom_tom = individu.famille('dom_tom', period)

        salaire_net = individu('salaire_net', period)

        return period, salaire_net * 0.9 - 100 * dom_tom


class salaire_net(Variable):
    column = FloatCol
    entity = Individu
    label = u"Salaire net"

    def function(individu, period):
        period = period.start.period(u'year').offset('first-of')
        salaire_brut = individu('salaire_brut', period)

        return period, salaire_brut * 0.8


class csg(Variable):
    column = FloatCol
    entity = Individu
    label = u"CSG payées sur le salaire"

    def function(individu, period, legislation):
        period = period.start.period(u'year').offset('first-of')
        taux = legislation(period).csg.activite.deductible.taux
        salaire_brut = individu('salaire_brut', period)

        return period, taux * salaire_brut


class TestTaxBenefitSystem(DummyTaxBenefitSystem):
    def __init__(self):
        DummyTaxBenefitSystem.__init__(self)

        # We cannot automatically import all the variable from this file, there would be an import loop
        self.add_variables(age_en_mois, birth, depcom, salaire_brut, age, dom_tom, revenu_disponible, revenu_disponible_famille, rsa, salaire_imposable, salaire_net, csg, af)


tax_benefit_system = TestTaxBenefitSystem()


def test_input_variable():
    year = 2016

    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = year,
        parent1 = dict(
            salaire_brut = 2000,
            ),
        ).new_simulation()
    assert_near(simulation.calculate('salaire_brut'), [2000])


def test_basic_calculation():
    year = 2016

    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = year,
        parent1 = dict(
            salaire_brut = 2000,
            ),
        ).new_simulation()
    assert_near(simulation.calculate('salaire_net'), [1600])


def test_params():
    year = 2013

    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = year,
        parent1 = dict(
            salaire_brut = 2000,
            ),
        ).new_simulation()
    assert_near(simulation.calculate('csg'), [102])


def test_1_axis():
    year = 2013
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        axes = [
            dict(
                count = 3,
                name = 'salaire_brut',
                max = 100000,
                min = 0,
                ),
            ],
        period = year,
        parent1 = {},
        parent2 = {},
        ).new_simulation(debug = True)
    assert_near(simulation.calculate('revenu_disponible_famille'), [7200, 28800, 54000], absolute_error_margin = 0.005)


def test_2_parallel_axes_1_constant():
    year = 2013
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        axes = [
            [
                dict(
                    count = 3,
                    name = 'salaire_brut',
                    max = 100000,
                    min = 0,
                    ),
                dict(
                    count = 3,
                    index = 1,
                    name = 'salaire_brut',
                    max = 0.0001,
                    min = 0,
                    ),
                ],
            ],
        period = year,
        parent1 = {},
        parent2 = {},
        ).new_simulation(debug = True)
    assert_near(simulation.calculate('revenu_disponible_famille'), [7200, 28800, 54000], absolute_error_margin = 0.005)


def test_2_parallel_axes_different_periods():
    year = 2013
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        axes = [
            [
                dict(
                    count = 3,
                    name = 'salaire_brut',
                    max = 120000,
                    min = 0,
                    period = year - 1,
                    ),
                dict(
                    count = 3,
                    index = 1,
                    name = 'salaire_brut',
                    max = 120000,
                    min = 0,
                    period = year,
                    ),
                ],
            ],
        period = year,
        parent1 = {},
        parent2 = {},
        ).new_simulation(debug = True)
    assert_near(simulation.calculate('salaire_brut', year - 1), [0, 0, 60000, 0, 120000, 0], absolute_error_margin = 0)
    assert_near(simulation.calculate('salaire_brut', '{}-01'.format(year - 1)), [0, 0, 5000, 0, 10000, 0],
        absolute_error_margin = 0)
    assert_near(simulation.calculate('salaire_brut', year), [0, 0, 0, 60000, 0, 120000], absolute_error_margin = 0)
    assert_near(simulation.calculate('salaire_brut', '{}-01'.format(year)), [0, 0, 0, 5000, 0, 10000],
        absolute_error_margin = 0)


def test_2_parallel_axes_same_values():
    year = 2013
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        axes = [
            [
                dict(
                    count = 3,
                    name = 'salaire_brut',
                    max = 100000,
                    min = 0,
                    ),
                dict(
                    count = 3,
                    index = 1,
                    name = 'salaire_brut',
                    max = 100000,
                    min = 0,
                    ),
                ],
            ],
        period = year,
        parent1 = {},
        parent2 = {},
        ).new_simulation(debug = True)
    assert_near(simulation.calculate('revenu_disponible_famille'), [7200, 50400, 100800], absolute_error_margin = 0.005)


def test_age():
    year = 2013
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = year,
        parent1 = dict(
            birth = datetime.date(year - 40, 1, 1),
            ),
        ).new_simulation(debug = True)
    assert_near(simulation.calculate('age'), [40], absolute_error_margin = 0.005)

    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = year,
        parent1 = dict(
            age_en_mois = 40 * 12 + 11,
            ),
        ).new_simulation(debug = True)
    assert_near(simulation.calculate('age'), [40], absolute_error_margin = 0.005)


def check_revenu_disponible(year, depcom, expected_revenu_disponible):
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        axes = [
            dict(
                count = 3,
                name = 'salaire_brut',
                max = 100000,
                min = 0,
                ),
            ],
        famille = dict(depcom = depcom),
        period = periods.period(year),
        parent1 = dict(),
        parent2 = dict(),
        ).new_simulation(debug = True)
    revenu_disponible = simulation.calculate('revenu_disponible')
    assert_near(revenu_disponible, expected_revenu_disponible, absolute_error_margin = 0.005)
    revenu_disponible_famille = simulation.calculate('revenu_disponible_famille')
    expected_revenu_disponible_famille = np.array([
        expected_revenu_disponible[i] + expected_revenu_disponible[i + 1]
        for i in range(0, len(expected_revenu_disponible), 2)
        ])
    assert_near(revenu_disponible_famille, expected_revenu_disponible_famille, absolute_error_margin = 0.005)


def test_revenu_disponible():
    yield check_revenu_disponible, 2009, '75101', np.array([0, 0, 25200, 0, 50400, 0])
    yield check_revenu_disponible, 2010, '75101', np.array([1200, 1200, 25200, 1200, 50400, 1200])
    yield check_revenu_disponible, 2011, '75101', np.array([2400, 2400, 25200, 2400, 50400, 2400])
    yield check_revenu_disponible, 2012, '75101', np.array([2400, 2400, 25200, 2400, 50400, 2400])
    yield check_revenu_disponible, 2013, '75101', np.array([3600, 3600, 25200, 3600, 50400, 3600])

    yield check_revenu_disponible, 2009, '97123', np.array([-70.0, -70.0, 25130.0, -70.0, 50330.0, -70.0])
    yield check_revenu_disponible, 2010, '97123', np.array([1130.0, 1130.0, 25130.0, 1130.0, 50330.0, 1130.0])
    yield check_revenu_disponible, 2011, '98456', np.array([2330.0, 2330.0, 25130.0, 2330.0, 50330.0, 2330.0])
    yield check_revenu_disponible, 2012, '98456', np.array([2330.0, 2330.0, 25130.0, 2330.0, 50330.0, 2330.0])
    yield check_revenu_disponible, 2013, '98456', np.array([3530.0, 3530.0, 25130.0, 3530.0, 50330.0, 3530.0])


def test_variable_with_reference():
    def new_simulation():
        return tax_benefit_system.new_scenario().init_single_entity(
            period = 2013,
            parent1 = dict(
                salaire_brut = 4000,
                ),
            ).new_simulation()

    revenu_disponible_avant_reforme = new_simulation().calculate('revenu_disponible', 2013)
    assert(revenu_disponible_avant_reforme > 0)

    class revenu_disponible(Variable):

        def function(self, simulation, period):
            return period, self.zeros()

    tax_benefit_system.update_variable(revenu_disponible)
    revenu_disponible_apres_reforme = new_simulation().calculate('revenu_disponible', 2013)

    assert(revenu_disponible_apres_reforme == 0)


@raises(VariableNameConflict)
def test_variable_name_conflict():
    class revenu_disponible(Variable):
        reference = 'revenu_disponible'

        def function(self, simulation, period):
            return period, self.zeros()
    tax_benefit_system.add_variable(revenu_disponible)


@raises(VariableNotFound)
def test_non_existing_variable():
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = 2013,
        parent1 = dict(),
        ).new_simulation()

    simulation.calculate('non_existent_variable', 2013)
