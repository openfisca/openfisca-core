# -*- coding: utf-8 -*-

import datetime

import numpy as np
from nose.tools import raises

from openfisca_core.variables import Variable
from openfisca_core.columns import YEAR
from openfisca_core.taxbenefitsystems import VariableNameConflict, VariableNotFound
from openfisca_core import periods
from dummy_country import DummyTaxBenefitSystem
from openfisca_core.tools import assert_near


tax_benefit_system = DummyTaxBenefitSystem()


def test_input_variable():
    year = 2016

    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = year,
        parent1 = dict(
            salaire_brut = 2000,
            ),
        ).new_simulation()
    assert_near(simulation.calculate_add('salaire_brut'), [2000], absolute_error_margin=0.01)


def test_basic_calculation():
    year = 2016

    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = year,
        parent1 = dict(
            salaire_brut = 2000,
            ),
        ).new_simulation()
    assert_near(simulation.calculate_add('salaire_net'), [1600], absolute_error_margin=0.01)


def test_params():
    year = 2013

    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = year,
        parent1 = dict(
            salaire_brut = 2000,
            ),
        ).new_simulation()
    assert_near(simulation.calculate('csg'), [102], absolute_error_margin=0.01)


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
    assert_near(simulation.calculate_add('salaire_brut', year - 1), [0, 0, 60000, 0, 120000, 0], absolute_error_margin = 0)
    assert_near(simulation.calculate('salaire_brut', '{}-01'.format(year - 1)), [0, 0, 5000, 0, 10000, 0],
        absolute_error_margin = 0)
    assert_near(simulation.calculate_add('salaire_brut', year), [0, 0, 0, 60000, 0, 120000], absolute_error_margin = 0)
    assert_near(simulation.calculate('salaire_brut', '{}-01'.format(year)), [0, 0, 0, 5000, 0, 10000],
        absolute_error_margin = 0)


def test_2_parallel_axes_same_values():
    year = 2013
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        axes = [
            [
                dict(
                    count = 3,
                    index = 0,
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
    print(simulation.calculate_add('salaire_brut'))
    assert_near(simulation.calculate('revenu_disponible_famille'), [7200, 50400, 100800], absolute_error_margin = 0.005)


def test_age():
    year = 2013
    month = '2013-01'
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = year,
        parent1 = dict(
            birth = datetime.date(year - 40, 1, 1),
            ),
        ).new_simulation(debug = True)
    assert_near(simulation.calculate('age', '2013-01'), [40], absolute_error_margin = 0.005)

    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = month,
        parent1 = dict(
            age_en_mois = 40 * 12 + 11,
            ),
        ).new_simulation(debug = True)
    assert_near(simulation.calculate('age', '2013-01'), [40], absolute_error_margin = 0.005)


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
        period_behavior = YEAR

        def function(self, simulation, period):
            return period, self.zeros()

    tax_benefit_system.update_variable(revenu_disponible)
    revenu_disponible_apres_reforme = new_simulation().calculate('revenu_disponible', 2013)

    assert(revenu_disponible_apres_reforme == 0)


@raises(VariableNameConflict)
def test_variable_name_conflict():
    class revenu_disponible(Variable):
        reference = 'revenu_disponible'
        period_behavior = YEAR

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
