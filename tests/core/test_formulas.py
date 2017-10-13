# -*- coding: utf-8 -*-


import numpy as np

from openfisca_core.periods import MONTH
from openfisca_core.variables import Variable
from openfisca_core.formula_helpers import switch
from openfisca_country_template import CountryTaxBenefitSystem
from openfisca_country_template.entities import Person


class choice(Variable):
    column = IntCol
    entity = Person
    definition_period = MONTH


class uses_multiplication(Variable):
    column = IntCol
    entity = Person
    label = u'Variable with formula that uses multiplication'
    definition_period = MONTH

    def formula(self, simulation, period):
        choice = simulation.calculate('choice', period)
        result = (choice == 1) * 80 + (choice == 2) * 90
        return result


class uses_switch(Variable):
    column = IntCol
    entity = Person
    label = u'Variable with formula that uses switch'
    definition_period = MONTH

    def formula(self, simulation, period):
        choice = simulation.calculate('choice', period)
        result = switch(
            choice,
            {
                1: 80,
                2: 90,
                },
            )
        return result


# TaxBenefitSystem instance declared after formulas
tax_benefit_system = CountryTaxBenefitSystem()
tax_benefit_system.add_variables(choice, uses_multiplication, uses_switch)
month = '2013-01'
scenario = tax_benefit_system.new_scenario().init_from_attributes(
    period = month,
    input_variables = {
        # 'choice': [1, 1, 1, 2],
        'choice': np.random.randint(2, size = 1000) + 1,
        },
    )


def test_switch():
    simulation = scenario.new_simulation(debug = True)
    uses_switch = simulation.calculate('uses_switch', period = month)
    assert isinstance(uses_switch, np.ndarray)


def test_multiplication():
    simulation = scenario.new_simulation(debug = True)
    uses_multiplication = simulation.calculate('uses_multiplication', period = month)
    assert isinstance(uses_multiplication, np.ndarray)


def test_compare_multiplication_and_switch():
    simulation = scenario.new_simulation(debug = True)
    uses_multiplication = simulation.calculate('uses_multiplication', period = month)
    uses_switch = simulation.calculate('uses_switch', period = month)
    assert np.all(uses_switch == uses_multiplication)
