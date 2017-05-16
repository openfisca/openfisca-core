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
from openfisca_core.columns import FloatCol


tax_benefit_system = CountryTaxBenefitSystem()


class income_tax_no_period(Variable):
    column = FloatCol
    entity = Person
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


# 371 - start_date, stop_date, one function > fixed_tax
def test_dated_variable_with_one_formula():
    year = 1985
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = year,
        parent1 = dict(
            birth = datetime.date(year - 20, 1, 1),
            ),
        ).new_simulation()
    assert (simulation.calculate('fixed_tax', year) == 400)

    var_fixed_tax = tax_benefit_system.column_by_name['fixed_tax']
    assert var_fixed_tax is not None

    assert var_fixed_tax.start == datetime.date(1980, 1, 1)
    assert var_fixed_tax.end == datetime.date(1989, 12, 31)

    assert var_fixed_tax.formula_class.dated_formulas_class.__len__() == 1
    fixed_tax_formula = var_fixed_tax.formula_class.dated_formulas_class[0]
    assert fixed_tax_formula is not None

    assert var_fixed_tax.start == fixed_tax_formula['start_instant'].date
    assert var_fixed_tax.end == fixed_tax_formula['stop_instant'].date


def has_dated_attributes(variable):
    return (variable.start is not None) and (variable.end is not None)


# 371 - @dated_function > rmi
def test_variable_with_one_formula():
    month = '2005-02'
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = month,
        parent1 = dict(
            salaire_imposable = {'2005': 10000},
            ),
        ).new_simulation()
    assert_near(simulation.calculate('rmi', month), [0], absolute_error_margin=0.01)

    var_rmi = tax_benefit_system.column_by_name['rmi']
    assert var_rmi is not None

    assert not has_dated_attributes(var_rmi)
    assert var_rmi.formula_class.dated_formulas_class.__len__() == 1

    rmi_formula = var_rmi.formula_class.dated_formulas_class[0]
    assert rmi_formula is not None
    assert rmi_formula['start_instant'].date == datetime.date(2000, 1, 1)
    assert rmi_formula['stop_instant'].date == datetime.date(2009, 12, 31)


# 371 - @dated_function without stop/different names > rsa
def test_variable_with_dated_formulas__different_names():
    dated_function_nb = 3
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = '2009',
        parent1 = dict(
            salaire_imposable = {'2010': 0,
                                 '2011': 15000,
                                 '2013': 15150,
                                 '2016': 17000},
            ),
        ).new_simulation()
    assert_near(simulation.calculate('rsa', '2010-05'), [100], absolute_error_margin=0.01)

    variable = tax_benefit_system.column_by_name['rsa']
    assert variable is not None
    assert not has_dated_attributes(variable)

    assert variable.formula_class.dated_formulas_class.__len__() == dated_function_nb
    i = 0
    for formula in variable.formula_class.dated_formulas_class:
        assert formula is not None, (dated_function_nb + " formulas expected in " + variable.formula_class.dated_formulas_class)
        # assert formula['formula_class'].holder is not None, ("Undefined holder for '" + variable.name + "', function#" + str(i))
        assert formula['start_instant'] is not None, ("Missing 'start' date on '" + variable.name + "', function#" + str(i))
        if i < (dated_function_nb - 1):
            assert formula['stop_instant'] is not None, ("Deprecated 'end' date but 'stop_instant' deduction expected on '" + variable.name + "', function#" + str(i))
        i += 1

    assert_near(simulation.calculate('rsa', '2011-05'), [0], absolute_error_margin=0.01)


# #371 - start_date, stop_date, @dated_function/different names > api
def test_dated_variable_with_formulas__different_names():
    month = '1999-01'
    dated_function_nb = 2
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = month,
        parent1 = dict(
            ),
        enfants = [
            dict(
                ),
            dict(
                ),
            ]
        ).new_simulation()
    assert_near(simulation.calculate('api', month), [0], absolute_error_margin=0.01)

    variable = tax_benefit_system.column_by_name['api']
    assert variable is not None
    assert has_dated_attributes(variable)

    assert variable.formula_class.dated_formulas_class.__len__() == dated_function_nb

    i = 0
    formula = variable.formula_class.dated_formulas_class[0]
    assert formula is not None, (dated_function_nb + " formulas expected in " + variable.formula_class.dated_formulas_class)
    assert formula['start_instant'] is not None, ("'start_instant' deduced from 'start' attribute expected on '" + variable.name + "', function#" + str(i))
    assert formula['start_instant'].date == variable.start

    i += 1
    formula = variable.formula_class.dated_formulas_class[1]
    assert formula is not None, (dated_function_nb + " formulas expected in " + variable.formula_class.dated_formulas_class)
    assert formula['stop_instant'] is not None, ("'stop_instant' deduced from 'stop' attribute expected on '" + variable.name + "', function#" + str(i))
    assert formula['stop_instant'].date == variable.end


# 371 - start_date, stop_date, @dated_function/one name > api_same_function_name
def test_dated_variable_with_formulas__same_name():
    month = '1999-01'
    dated_function_nb = 2
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = month,
        parent1 = dict(
            ),
        enfants = [
            dict(
                ),
            dict(
                ),
            ]
        ).new_simulation()
    assert_near(simulation.calculate('api_same_function_name', month), [0], absolute_error_margin=0.01)

    variable = tax_benefit_system.column_by_name['api_same_function_name']
    assert variable is not None
    assert has_dated_attributes(variable)

    # Should take the first function declared only.
    assert variable.formula_class.dated_formulas_class.__len__() == 1

    i = 0
    formula = variable.formula_class.dated_formulas_class[0]
    assert formula is not None, (dated_function_nb + " formulas expected in " + variable.formula_class.dated_formulas_class)
    assert formula['start_instant'] is not None, ("'start_instant' deduced from 'start' attribute expected on '" + variable.name + "', function#" + str(i))
    assert formula['start_instant'].date == variable.start

    # Should apply stop_date attribute to the first function declared.
    assert formula['stop_instant'] is not None, ("'stop_instant' deduced from 'stop' attribute expected on '" + variable.name + "', function#" + str(i))
    assert formula['stop_instant'].date == variable.end


# 371 - start_date, stop_date, @dated_function/stop_date older than function start > api_stop_date_before_function_start
def test_dated_variable_with_formulas__stop_date_older():
    month = '1999-01'
    dated_function_nb = 2
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = month,
        parent1 = dict(
            ),
        enfants = [
            dict(
                ),
            dict(
                ),
            ]
        ).new_simulation()
    assert_near(simulation.calculate('api_stop_date_before_function_start', month), [0], absolute_error_margin=0.01)

    variable = tax_benefit_system.column_by_name['api_stop_date_before_function_start']
    assert variable is not None
    assert has_dated_attributes(variable)

    # Should take the first function declared only.
    assert variable.formula_class.dated_formulas_class.__len__() == 1

    i = 0
    formula = variable.formula_class.dated_formulas_class[0]
    assert formula is not None, (dated_function_nb + " formulas expected in " + variable.formula_class.dated_formulas_class)
    assert formula['start_instant'] is not None, ("'start_instant' deduced from 'start' attribute expected on '" + variable.name + "', function#" + str(i))
    assert formula['start_instant'].date == variable.start

    # Should apply stop_date attribute to the first function declared even if it inactivates it.
    assert formula['stop_instant'] is not None, ("'stop_date' older than 'start_instant' shouldn't be applied on '" + variable.name + "', function#" + str(i))
    assert formula['stop_instant'].date == variable.end
