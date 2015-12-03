# -*- coding: utf-8 -*-

import datetime

from nose.tools import assert_equal

from .. import columns, periods, reforms
from ..formulas import neutralize_column, dated_function
from ..tools import assert_near
from .dummy_country import Familles
from .test_countries import tax_benefit_system


def test_formula_neutralization():
    Reform = reforms.make_reform(
        key = u'test_rsa_neutralization',
        name = u'Test rsa neutralization',
        reference = tax_benefit_system,
        )
    Reform.add_column(neutralize_column(tax_benefit_system.column_by_name['rsa']))
    reform = Reform()

    year = 2013
    scenario = reform.new_scenario().init_single_entity(
        period = year,
        famille = dict(depcom = '75101'),
        parent1 = dict(),
        parent2 = dict(),
        )
    simulation = scenario.new_simulation(debug = True, reference = True)
    rsa = simulation.calculate('rsa', period = '2013-01')
    assert_near(rsa, 300, absolute_error_margin = 0)
    revenu_disponible = simulation.calculate('revenu_disponible')
    assert_near(revenu_disponible, 3600, absolute_error_margin = 0)

    reform_simulation = scenario.new_simulation(debug = True)
    rsa_reform = reform_simulation.calculate('rsa', period = '2013-01')
    assert_near(rsa_reform, 0, absolute_error_margin = 0)
    revenu_disponible_reform = reform_simulation.calculate('revenu_disponible')
    assert_near(revenu_disponible_reform, 0, absolute_error_margin = 0)

    # def test_input_variable_neutralization():
    Reform = reforms.make_reform(
        key = u'test_salaire_brut_neutralization',
        name = u'Test salaire_brut neutralization',
        reference = tax_benefit_system,
        )
    Reform.add_column(neutralize_column(tax_benefit_system.column_by_name['salaire_brut']))
    reform = Reform()

    year = 2013
    scenario = reform.new_scenario().init_single_entity(
        period = year,
        famille = dict(depcom = '75101'),
        parent1 = dict(
            salaire_brut = 120000,
            ),
        parent2 = dict(
            salaire_brut = 60000,
            ),
        )
    simulation = scenario.new_simulation(debug = True, reference = True)
    salaire_brut_annuel = simulation.calculate('salaire_brut')
    assert_near(salaire_brut_annuel, [120000, 60000], absolute_error_margin = 0)
    salaire_brut_mensuel = simulation.calculate('salaire_brut', period = '2013-01')
    assert_near(salaire_brut_mensuel, [10000, 5000], absolute_error_margin = 0)
    revenu_disponible = simulation.calculate('revenu_disponible')
    assert_near(revenu_disponible, [60480, 30240], absolute_error_margin = 0)

    reform_simulation = scenario.new_simulation(debug = True)
    salaire_brut_annuel_reform = reform_simulation.calculate('salaire_brut')
    assert_near(salaire_brut_annuel_reform, [0, 0], absolute_error_margin = 0)
    salaire_brut_mensuel_reform = reform_simulation.calculate('salaire_brut', period = '2013-01')
    assert_near(salaire_brut_mensuel_reform, [0, 0], absolute_error_margin = 0)
    revenu_disponible_reform = reform_simulation.calculate('revenu_disponible')
    assert_near(revenu_disponible_reform, [3600, 3600], absolute_error_margin = 0)


def test_updated_legislation_items():
    def check_updated_legislation_items(description, items, start_instant, stop_instant, value, expected_items):
        new_items = reforms.updated_legislation_items(items, start_instant, stop_instant, value)
        assert_equal(map(dict, new_items), expected_items)

    # yield(
    #     check_updated_legislation_items,
    #     u'Insert a new item before the first existing item',
    #     [
    #         {
    #             "start": "2012-01-01",
    #             "stop": "2013-12-31",
    #             "value": 0.0,
    #             },
    #         ],
    #     periods.period('year', 2010).start,
    #     periods.period('year', 2010).stop,
    #     1,
    #     [
    #         {
    #             "start": "2010-01-01",
    #             "stop": "2010-12-31",
    #             "value": 1.0,
    #             },
    #         {
    #             "start": "2012-01-01",
    #             "stop": "2013-12-31",
    #             "value": 0.0,
    #             },
    #         ],
    #     )
    # yield(
    #     check_updated_legislation_items,
    #     u'Insert a new item after the last existing item',
    #     [
    #         {
    #             "start": "2012-01-01",
    #             "stop": "2013-12-31",
    #             "value": 0.0,
    #             },
    #         ],
    #     periods.period('year', 2014).start,
    #     periods.period('year', 2014).stop,
    #     1,
    #     [
    #         {
    #             "start": "2012-01-01",
    #             "stop": "2013-12-31",
    #             "value": 0.0,
    #             },
    #         {
    #             "start": "2014-01-01",
    #             "stop": "2014-12-31",
    #             "value": 1.0,
    #             },
    #         ],
    #     )
    yield(
        check_updated_legislation_items,
        u'Replace an item by a new item',
        [
            {
                "start": "2013-01-01",
                "stop": "2013-12-31",
                "value": 0.0,
                },
            ],
        periods.period('year', 2013).start,
        periods.period('year', 2013).stop,
        1,
        [
            {
                "start": "2013-01-01",
                "stop": "2013-12-31",
                "value": 1.0,
                },
            ],
        )
    yield(
        check_updated_legislation_items,
        u'Insert a new item in the middle of an existing item',
        [
            {
                "start": "2010-01-01",
                "stop": "2013-12-31",
                "value": 0.0,
                },
            ],
        periods.period('year', 2011).start,
        periods.period('year', 2011).stop,
        1,
        [
            {
                "start": "2010-01-01",
                "stop": "2010-12-31",
                "value": 0.0,
                },
            {
                "start": "2011-01-01",
                "stop": "2011-12-31",
                "value": 1.0,
                },
            {
                "start": "2012-01-01",
                "stop": "2013-12-31",
                "value": 0.0,
                },
            ],
        )


def test_add_variable():
    Reform = reforms.make_reform(
        key = 'test_add_variable',
        name = "Test",
        reference = tax_benefit_system,
        )

    class nouvelle_variable(Reform.Variable):
        column = columns.IntCol
        label = u"Nouvelle variable introduite par la réforme"
        entity_class = Familles

        def function(self, simulation, period):
            return period, self.zeros() + 10

    year = 2013
    reform = Reform()
    scenario = reform.new_scenario().init_single_entity(
        period = year,
        parent1 = dict(),
        )

    assert 'nouvelle_variable' not in tax_benefit_system.column_by_name
    reform_simulation = scenario.new_simulation(debug = True)
    nouvelle_variable1 = reform_simulation.calculate('nouvelle_variable', period = '2013-01')
    assert_near(nouvelle_variable1, 10, absolute_error_margin = 0)


def test_add_dated_variable():
    Reform = reforms.make_reform(
        key = 'test_add_variable',
        name = "Test",
        reference = tax_benefit_system,
        )

    class nouvelle_dated_variable(Reform.DatedVariable):
        column = columns.IntCol
        label = u"Nouvelle variable introduite par la réforme"
        entity_class = Familles

        @dated_function(datetime.date(2010, 1, 1))
        def function_2010(self, simulation, period):
            return period, self.zeros() + 10

        @dated_function(datetime.date(2011, 1, 1))
        def function_apres_2011(self, simulation, period):
            return period, self.zeros() + 15

    reform = Reform()
    scenario = reform.new_scenario().init_single_entity(
        period = 2013,
        parent1 = dict(),
        )

    reform_simulation = scenario.new_simulation(debug = True)
    nouvelle_dated_variable1 = reform_simulation.calculate('nouvelle_dated_variable', period = '2013-01')
    assert_near(nouvelle_dated_variable1, 15, absolute_error_margin = 0)


def test_add_variable_with_reference():
    Reform = reforms.make_reform(
        key = 'test_add_variable_with_reference',
        name = "Test",
        reference = tax_benefit_system,
        )

    class revenu_disponible(Reform.Variable):
        reference = tax_benefit_system.column_by_name['revenu_disponible']

        def function(self, simulation, period):
            return period, self.zeros() + 10

    year = 2013
    reform = Reform()
    scenario = reform.new_scenario().init_single_entity(
        period = year,
        parent1 = dict(),
        )

    assert 'revenu_disponible' in tax_benefit_system.column_by_name
    assert revenu_disponible.entity_class.key_plural == \
        tax_benefit_system.column_by_name['revenu_disponible'].entity_class.key_plural, revenu_disponible.entity_class
    assert revenu_disponible.name == tax_benefit_system.column_by_name['revenu_disponible'].name, \
        revenu_disponible
    assert revenu_disponible.label == tax_benefit_system.column_by_name['revenu_disponible'].label, \
        revenu_disponible.label

    reform_simulation = scenario.new_simulation(debug = True)
    revenu_disponible1 = reform_simulation.calculate('revenu_disponible', period = '2013-01')
    assert_near(revenu_disponible1, 10, absolute_error_margin = 0)
