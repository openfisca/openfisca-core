# -*- coding: utf-8 -*-

from pytest import raises

from openfisca_core.variables import Variable
from openfisca_core.periods import MONTH
from openfisca_core.taxbenefitsystems import VariableNameConflict, VariableNotFound
from openfisca_core import periods
from openfisca_core.populations import DIVIDE
from openfisca_core.tools import assert_near


def test_input_variable(make_simulation, period):
    simulation = make_simulation({'salary': 2000})
    assert_near(simulation.calculate('salary', period), [2000], absolute_error_margin = 0.01)


def test_basic_calculation(make_simulation, period):
    simulation = make_simulation({'salary': 2000})
    assert_near(simulation.calculate('income_tax', period), [300], absolute_error_margin = 0.01)


def test_calculate_add(make_simulation, period):
    simulation = make_simulation({'salary': 24000})
    assert_near(simulation.calculate_add('income_tax', period), [3600], absolute_error_margin = 0.01)


def test_calculate_divide(make_simulation, period):
    simulation = make_simulation({
        'accommodation_size': 100,
        'housing_occupancy_status': 'tenant',
        })
    assert_near(simulation.calculate_divide('housing_tax', period), [1000 / 12.], absolute_error_margin = 0.01)


def test_bareme(make_simulation, period):
    simulation = make_simulation({'salary': 20000})
    expected_result = 0.02 * 6000 + 0.06 * 6400 + 0.12 * 7600
    assert_near(simulation.calculate('social_security_contribution', period), [expected_result], absolute_error_margin = 0.01)


def test_non_existing_variable(make_simulation):
    simulation = make_simulation({})
    with raises(VariableNotFound):
        simulation.calculate('non_existent_variable', 2013)


def test_calculate_variable_with_wrong_definition_period(make_simulation):
    simulation = make_simulation({})

    with raises(ValueError) as error:
        simulation.calculate('basic_income', 2016)

    error_message = str(error.value)
    expected_words = ['period', '2016', 'month', 'basic_income', 'ADD']

    for word in expected_words:
        assert word in error_message, 'Expected "{}" in error message "{}"'.format(word, error_message)


def test_divide_option_on_month_defined_variable(make_simulation):
    simulation = make_simulation({})
    with raises(ValueError):
        simulation.person('disposable_income', "2016-01", options = [DIVIDE])


def test_divide_option_with_complex_period(make_simulation):
    simulation = make_simulation({})
    quarter = periods.period('2013-12').last_3_months
    with raises(ValueError):
        simulation.household('housing_tax', quarter, options = [DIVIDE])


def test_input_with_wrong_period(make_simulation):
    with raises(ValueError):
        make_simulation({'basic_income': {2015: 12000}})


def test_variable_with_reference(tax_benefit_system, make_isolated_simulation):
    simulation_base = make_isolated_simulation(tax_benefit_system, {'salary': 4000})

    revenu_disponible_avant_reforme = simulation_base.calculate('disposable_income', "2016-01")
    assert(revenu_disponible_avant_reforme > 0)

    class disposable_income(Variable):
        definition_period = MONTH

        def formula(household, period):
            return household.empty_array()

    tax_benefit_system.update_variable(disposable_income)

    simulation_reform = make_isolated_simulation(tax_benefit_system, {'salary': 4000})
    revenu_disponible_apres_reforme = simulation_reform.calculate('disposable_income', "2016-01")

    assert(revenu_disponible_apres_reforme == 0)


def test_variable_name_conflict(tax_benefit_system):
    class disposable_income(Variable):
        reference = 'disposable_income'
        definition_period = MONTH

        def formula(household, period):
            return household.empty_array()
    with raises(VariableNameConflict):
        tax_benefit_system.add_variable(disposable_income)
