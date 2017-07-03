# -*- coding: utf-8 -*-

import warnings


from nose.tools import raises
from nose.tools import assert_equal

from openfisca_core import columns, periods, reforms
from openfisca_core.periods import MONTH
from openfisca_core.reforms import Reform
from openfisca_core.variables import Variable
from openfisca_core.periods import Instant
from openfisca_core.tools import assert_near
from openfisca_country_template.entities import Household
from openfisca_country_template import CountryTaxBenefitSystem
tax_benefit_system = CountryTaxBenefitSystem()


class test_basic_income_neutralization(Reform):
    def apply(self):
        self.neutralize_variable('basic_income')


def test_formula_neutralization():
    reform = test_basic_income_neutralization(tax_benefit_system)

    period = '2017-01'
    scenario = reform.new_scenario().init_from_attributes(
        period = period
        )
    simulation = scenario.new_simulation(debug = True, use_baseline = True)
    basic_income = simulation.calculate('basic_income', period = period)
    assert_near(basic_income, 600)
    disposable_income = simulation.calculate('disposable_income', period = period)
    assert disposable_income > 0

    reform_simulation = scenario.new_simulation(debug = True)
    basic_income_reform = reform_simulation.calculate('basic_income', period = '2013-01')
    assert_near(basic_income_reform, 0, absolute_error_margin = 0)
    disposable_income_reform = reform_simulation.calculate('disposable_income', period = period)
    assert_near(disposable_income_reform, 0)


def test_neutralization_optimization():
    reform = test_basic_income_neutralization(tax_benefit_system)

    period = '2017-01'
    scenario = reform.new_scenario().init_from_attributes(
        period = period,
        )
    simulation = scenario.new_simulation(debug = True)
    simulation.calculate('basic_income', period = '2013-01')
    simulation.calculate_add('basic_income', period = '2013')

    # As basic_income is neutralized, it should not be cached
    basic_income_holder = simulation.persons.get_holder('basic_income')
    assert basic_income_holder._array_by_period is None


def test_input_variable_neutralization():

    class test_salary_neutralization(Reform):
        def apply(self):
            self.neutralize_variable('salary')

    reform = test_salary_neutralization(tax_benefit_system)

    period = '2017-01'
    scenario = reform.new_scenario().init_from_attributes(
        period = period,
        input_variables = dict(salary = [1200, 1000])
        )

    reform = test_salary_neutralization(tax_benefit_system)

    with warnings.catch_warnings(record=True) as raised_warnings:
        reform_simulation = scenario.new_simulation()
        assert 'You cannot set a value for the variable' in raised_warnings[0].message.message
    salary = reform_simulation.calculate('salary', period)
    assert_near(salary, [0, 0],)
    disposable_income_reform = reform_simulation.calculate('disposable_income', period = period)
    assert_near(disposable_income_reform, [600, 600])


def test_permanent_variable_neutralization():

    class test_date_naissance_neutralization(Reform):
        def apply(self):
            self.neutralize_variable('birth')

    reform = test_date_naissance_neutralization(tax_benefit_system)

    year = 2013
    scenario = reform.new_scenario().init_from_attributes(
        period = year,
        input_variables = dict(
            birth = '1980-01-01'
            ),
        )
    simulation = scenario.new_simulation(use_baseline = True)
    with warnings.catch_warnings(record=True) as raised_warnings:
        reform_simulation = scenario.new_simulation()
        assert 'You cannot set a value for the variable' in raised_warnings[0].message.message
    assert str(simulation.calculate('birth', None)[0]) == '1980-01-01'
    assert str(reform_simulation.calculate('birth', None)[0]) == '1970-01-01'


def test_update_items():
    def check_update_items(description, items, start_instant, stop_instant, value, expected_items):
        new_items = reforms.update_items(items, start_instant, stop_instant, value)
        assert_equal(map(dict, new_items), expected_items)

    yield (
        check_update_items,
        u'Replace an item by a new item',
        [
            {"start": "2014-01-01", },
            {"start": "2013-01-01", "value": 0.0},
            ],
        periods.period(2013).start,
        periods.period(2013).stop,
        1.0,
        [
            {"start": "2014-01-01", },
            {"start": "2013-01-01", "value": 1.0},
            ],
        )
    yield (
        check_update_items,
        u'Replace an item by a new item in a list of items, the last being open',
        [
            {'start': u'2016-01-01', 'value': 9.67},
            {'start': u'2015-01-01', 'value': 9.61},
            {'start': u'2014-01-01', 'value': 9.53},
            ],
        periods.period(2015).start,
        periods.period(2015).stop,
        1.0,
        [
            {'start': u'2016-01-01', 'value': 9.67},
            {'start': u'2015-01-01', 'value': 1.0},
            {'start': u'2014-01-01', 'value': 9.53},
            ],
        )
    yield (
        check_update_items,
        u'Open the stop instant to the future',
        [
            {"start": "2014-01-01", },
            {"start": "2013-01-01", "value": 0.0},
            ],
        periods.period(2013).start,
        None,  # stop instant
        1.0,
        [{"start": "2013-01-01", "value": 1.0}],
        )
    yield (
        check_update_items,
        u'Insert a new item in the middle of an existing item',
        [
            {"start": "2014-01-01", },
            {"start": "2010-01-01", "value": 0.0},
            ],
        periods.period(2011).start,
        periods.period(2011).stop,
        1.0,
        [
            {"start": "2014-01-01", },
            {"start": "2012-01-01", "value": 0.0},
            {"start": "2011-01-01", "value": 1.0},
            {"start": "2010-01-01", "value": 0.0},
            ],
        )
    yield (
        check_update_items,
        u'Insert a new open item coming after the last open item',
        [
            {"start": "2014-01-01", "value": 0.14},
            {"start": "2006-01-01", "value": 0.055},
            ],
        periods.period(2015).start,
        None,  # stop instant
        1.0,
        [
            {"start": "2015-01-01", "value": 1},
            {"start": "2014-01-01", "value": 0.14},
            {"start": "2006-01-01", "value": 0.055},
            ],
        )
    yield (
        check_update_items,
        u'Insert a new item starting at the same date than the last open item',
        [
            {"start": "2014-01-01", "value": 0.14},
            {"start": "2006-01-01", "value": 0.055},
            ],
        periods.period(2014).start,
        periods.period(2014).stop,
        1.0,
        [
            {"start": "2015-01-01", "value": 0.14},
            {"start": "2014-01-01", "value": 1.0},
            {"start": "2006-01-01", "value": 0.055},
            ],
        )
    yield (
        check_update_items,
        u'Insert a new open item starting at the same date than the last open item',
        [
            {"start": "2014-01-01", "value": 0.14},
            {"start": "2006-01-01", "value": 0.055},
            ],
        periods.period(2014).start,
        None,  # stop instant
        1.0,
        [
            {"start": "2014-01-01", "value": 1.0},
            {"start": "2006-01-01", "value": 0.055},
            ],
        )
    yield (
        check_update_items,
        u'Insert a new item coming before the first item',
        [
            {"start": "2014-01-01", "value": 0.14},
            {"start": "2006-01-01", "value": 0.055},
            ],
        periods.period(2005).start,
        periods.period(2005).stop,
        1.0,
        [
            {"start": "2014-01-01", "value": 0.14},
            {"start": "2006-01-01", "value": 0.055},
            {"start": "2005-01-01", "value": 1.0},
            ],
        )
    yield (
        check_update_items,
        u'Insert a new item coming before the first item with a hole',
        [
            {"start": "2014-01-01", "value": 0.14},
            {"start": "2006-01-01", "value": 0.055},
            ],
        periods.period(2003).start,
        periods.period(2003).stop,
        1.0,
        [
            {"start": "2014-01-01", "value": 0.14},
            {"start": "2006-01-01", "value": 0.055},
            {"start": "2004-01-01", },
            {"start": "2003-01-01", "value": 1.0},
            ],
        )
    yield (
        check_update_items,
        u'Insert a new open item starting before the start date of the first item',
        [
            {"start": "2014-01-01", "value": 0.14},
            {"start": "2006-01-01", "value": 0.055},
            ],
        periods.period(2005).start,
        None,  # stop instant
        1.0,
        [{"start": "2005-01-01", "value": 1.0}],
        )
    yield (
        check_update_items,
        u'Insert a new open item starting at the same date than the first item',
        [
            {"start": "2014-01-01", "value": 0.14},
            {"start": "2006-01-01", "value": 0.055},
            ],
        periods.period(2006).start,
        None,  # stop instant
        1.0,
        [{"start": "2006-01-01", "value": 1.0}],
        )


def test_add_variable():

    class new_variable(Variable):
        column = columns.IntCol
        label = u"Nouvelle variable introduite par la réforme"
        entity = Household
        definition_period = MONTH

        def formula(self, simulation, period):
            return self.zeros() + 10

    class test_add_variable(Reform):

        def apply(self):
            self.add_variable(new_variable)

    reform = test_add_variable(tax_benefit_system)

    year = 2013

    scenario = reform.new_scenario().init_from_attributes(
        period = year,
        )

    assert tax_benefit_system.get_column('new_variable') is None
    reform_simulation = scenario.new_simulation(debug = True)
    new_variable1 = reform_simulation.calculate('new_variable', period = '2013-01')
    assert_near(new_variable1, 10, absolute_error_margin = 0)


def test_add_dated_variable():
    class new_dated_variable(Variable):
        column = columns.IntCol
        label = u"Nouvelle variable introduite par la réforme"
        entity = Household
        definition_period = MONTH

        def formula_2010_01_01(self, simulation, period):
            return self.zeros() + 10

        def formula_2011_01_01(self, simulation, period):
            return self.zeros() + 15

    class test_add_variable(Reform):
        def apply(self):
            self.add_variable(new_dated_variable)

    reform = test_add_variable(tax_benefit_system)

    scenario = reform.new_scenario().init_from_attributes(
        period = 2013,
        )

    reform_simulation = scenario.new_simulation(debug = True)
    new_dated_variable1 = reform_simulation.calculate('new_dated_variable', period = '2013-01')
    assert_near(new_dated_variable1, 15, absolute_error_margin = 0)


def test_update_variable():

    class disposable_income(Variable):
        definition_period = MONTH

        def formula(self, simulation, period):
            return self.zeros() + 10

    class test_update_variable(Reform):
        def apply(self):
            self.update_variable(disposable_income)

    reform = test_update_variable(tax_benefit_system)

    year = 2013
    scenario = reform.new_scenario().init_from_attributes(
        period = year,
        )

    disposable_income_reform = reform.get_column('disposable_income')
    disposable_income_reference = tax_benefit_system.get_column('disposable_income')

    assert disposable_income_reform is not None
    assert disposable_income_reform.entity.plural == disposable_income_reference.entity.plural
    assert disposable_income_reform.name == disposable_income_reference.name
    assert disposable_income_reform.label == disposable_income_reference.label

    reform_simulation = scenario.new_simulation()
    disposable_income1 = reform_simulation.calculate('disposable_income', period = '2013-01')
    assert_near(disposable_income1, 10, absolute_error_margin = 0)


@raises(Exception)
def test_wrong_reform():
    class wrong_reform(Reform):
        # A Reform must implement an `apply` method
        pass

    wrong_reform(tax_benefit_system)


def test_compose_reforms():

    class first_reform(Reform):
        class new_variable(Variable):
            column = columns.IntCol
            label = u"Nouvelle variable introduite par la réforme"
            entity = Household
            definition_period = MONTH

            def formula(self, simulation, period):
                return self.zeros() + 10

        def apply(self):
            self.add_variable(self.new_variable)

    class second_reform(Reform):
        class new_variable(Variable):
            column = columns.IntCol
            label = u"Nouvelle variable introduite par la réforme"
            entity = Household
            definition_period = MONTH

            def formula(self, simulation, period):
                return self.zeros() + 20

        def apply(self):
            self.update_variable(self.new_variable)

    reform = reforms.compose_reforms([first_reform, second_reform], tax_benefit_system)
    year = 2013
    scenario = reform.new_scenario().init_from_attributes(
        period = year,
        )

    reform_simulation = scenario.new_simulation(debug = True)
    new_variable1 = reform_simulation.calculate('new_variable', period = '2013-01')
    assert_near(new_variable1, 20, absolute_error_margin = 0)


def test_modify_legislation():

    def modify_legislation_json(reference_legislation_json_copy):
        reform_legislation_subtree = {
            "@type": "Node",
            "description": "Node added to the legislation by the reform",
            "children": {
                "new_param": {
                    "@type": "Parameter",
                    "description": "New parameter",
                    "format": "boolean",
                    "values": [
                        {'start': u'2015-01-01'},
                        {'start': u'2000-01-01', 'value': True}
                        ],
                    },
                },
            }
        reference_legislation_json_copy['children']['new_node'] = reform_legislation_subtree
        return reference_legislation_json_copy

    class test_modify_legislation(Reform):
        def apply(self):
            self.modify_legislation_json(modifier_function = modify_legislation_json)

    reform = test_modify_legislation(tax_benefit_system)

    legislation_new_node = reform.get_legislation()['children']['new_node']
    assert legislation_new_node is not None

    instant = Instant((2013, 1, 1))
    compact_legislation = reform.get_compact_legislation(instant)
    assert compact_legislation.new_node.new_param is True
