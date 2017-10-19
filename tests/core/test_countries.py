# -*- coding: utf-8 -*-

from nose.tools import raises, assert_raises

from openfisca_core.variables import Variable
from openfisca_core.periods import MONTH
from openfisca_core.taxbenefitsystems import VariableNameConflict, VariableNotFound
from openfisca_core import periods
from openfisca_core.formulas import DIVIDE
from openfisca_country_template import CountryTaxBenefitSystem
from openfisca_country_template.entities import Person
from openfisca_core.tools import assert_near


tax_benefit_system = CountryTaxBenefitSystem()


class income_tax_no_period(Variable):
    value_type = 'Float'
    entity = Person
    label = u"Salaire net (buggy)"
    definition_period = MONTH

    def formula(individu, period):
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

        def formula(self, simulation, period):
            return self.zeros()

    tax_benefit_system.update_variable(disposable_income)
    revenu_disponible_apres_reforme = new_simulation().calculate('disposable_income', "2016-01")

    assert(revenu_disponible_apres_reforme == 0)


@raises(VariableNameConflict)
def test_variable_name_conflict():
    class disposable_income(Variable):
        reference = 'disposable_income'
        definition_period = MONTH

        def formula(self, simulation, period):
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
