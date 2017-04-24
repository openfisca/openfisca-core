# -*- coding: utf-8 -*-

import datetime

import numpy as np
from nose.tools import raises, assert_raises

from openfisca_core.variables import Variable
from openfisca_core.periods import MONTH
from openfisca_core.taxbenefitsystems import VariableNameConflict, VariableNotFound
from openfisca_core import periods
from openfisca_core.formulas import DIVIDE
from openfisca_country_template import CountryTaxBenefitSystem
from openfisca_core.tools import assert_near
from openfisca_core.columns import FloatCol
from openfisca_dummy_country.entities import Individu


tax_benefit_system = CountryTaxBenefitSystem()


class income_tax_no_period(Variable):
    column = FloatCol
    entity = Individu
    label = u"Salaire net (buggy)"
    definition_period = MONTH

    def function(individu, period):
        # salary = individu('salary', period)  # correct
        salary = individu('salary')            # buggy

        return salary * 0.15


@raises(ValueError)
def test_no_period():
    year = 2016

    buggy_tbf = CountryTaxBenefitSystem()
    buggy_tbf.add_variable(income_tax_no_period)

    simulation = buggy_tbf.new_scenario().init_from_attributes(
        period = year,
        input_variables = dict(
            salary = 2000,
            ),
        ).new_simulation()
    simulation.calculate_add('income_tax_no_period', year)


def test_input_variable():
    period = "2016-01"
    simulation = tax_benefit_system.new_scenario().init_from_attributes(
    period = period,
    input_variables = {
        'salary': 2000,
        },
    ).new_simulation()
    assert_near(simulation.calculate_add('salary', period), [2000], absolute_error_margin = 0.01)


def test_basic_calculation():
    period = "2016-01"
    simulation = tax_benefit_system.new_scenario().init_from_attributes(
        period = period,
        input_variables = dict(
            salary = 2000,
            ),
        ).new_simulation()
    assert_near(simulation.calculate_add('income_tax', period), [300], absolute_error_margin = 0.01)


def test_bareme():
    period = "2016-01"
    simulation = tax_benefit_system.new_scenario().init_from_attributes(
        period = period,
        input_variables = dict(
            salary = 20000,
            ),
        ).new_simulation()
    expected_result = 0.02 * 6000 + 0.06 * 6400 + 0.12 * 7600
    assert_near(simulation.calculate('social_security_contribution', period), [expected_result], absolute_error_margin = 0.01)


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
    assert_near(simulation.calculate('revenu_disponible_famille', year), [7200, 28800, 54000], absolute_error_margin = 0.005)


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
    assert_near(simulation.calculate('revenu_disponible_famille', year), [7200, 28800, 54000], absolute_error_margin = 0.005)


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
    assert_near(simulation.calculate('revenu_disponible_famille', year), [7200, 50400, 100800], absolute_error_margin = 0.005)


def check_revenu_disponible(year, city_code, expected_revenu_disponible):
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        axes = [
            dict(
                count = 3,
                name = 'salaire_brut',
                max = 100000,
                min = 0,
                ),
            ],
        famille = dict(city_code = city_code),
        period = periods.period(year),
        parent1 = dict(),
        parent2 = dict(),
        ).new_simulation(debug = True)
    revenu_disponible = simulation.calculate('revenu_disponible', year)
    assert_near(revenu_disponible, expected_revenu_disponible, absolute_error_margin = 0.005)
    revenu_disponible_famille = simulation.calculate('revenu_disponible_famille', year)
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
        return tax_benefit_system.new_scenario().init_from_attributes(
            period = "2016-01",
            input_variables = dict(
                salary = 4000,
                ),
            ).new_simulation()

    revenu_disponible_avant_reforme = new_simulation().calculate('disposable_income', "2016-01")
    assert(revenu_disponible_avant_reforme > 0)

    class disposable_income(Variable):
        definition_period = MONTH

        def function(self, simulation, period):
            return self.zeros()

    tax_benefit_system.update_variable(disposable_income)
    revenu_disponible_apres_reforme = new_simulation().calculate('disposable_income', "2016-01")

    assert(revenu_disponible_apres_reforme == 0)


@raises(VariableNameConflict)
def test_variable_name_conflict():
    class disposable_income(Variable):
        reference = 'disposable_income'
        definition_period = MONTH

        def function(self, simulation, period):
            return self.zeros()
    tax_benefit_system.add_variable(disposable_income)


@raises(VariableNotFound)
def test_non_existing_variable():
    simulation = tax_benefit_system.new_scenario().init_from_attributes(
        period = "2016-01",
        ).new_simulation()

    simulation.calculate('non_existent_variable', 2013)


def test_calculate_variable_with_wrong_definition_period():
    simulation = tax_benefit_system.new_scenario().init_from_attributes(
        period = "2016-01"
        ).new_simulation()

    with assert_raises(ValueError) as error:
        simulation.calculate('basic_income', 2016)

    error_message = str(error.exception)
    expected_words = ['period', '2016', 'month', 'basic_income', 'ADD']

    for word in expected_words:
        assert word in error_message, u'Expected "{}" in error message "{}"'.format(word, error_message).encode('utf-8')


@raises(ValueError)
def test_divide_option_on_month_defined_variable():
    simulation = tax_benefit_system.new_scenario().init_from_attributes(
        period = "2016-01"
        ).new_simulation()

    simulation.person('disposable_income', "2016-01", options = [DIVIDE])


@raises(ValueError)
def test_divide_option_with_complex_period():
    simulation = tax_benefit_system.new_scenario().init_from_attributes(
        period = "2016-01"
        ).new_simulation()

    quarter = periods.period('2013-12').last_3_months
    simulation.household('housing_tax', quarter, options = [DIVIDE])


@raises(ValueError)
def test_input_with_wrong_period():
    tax_benefit_system.new_scenario().init_from_attributes(
        period = 2013,
        input_variables = dict(
            basic_income = {2015: 12000},
            ),
        ).new_simulation()
