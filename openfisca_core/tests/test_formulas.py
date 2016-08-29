# -*- coding: utf-8 -*-


import numpy as np

from openfisca_core.columns import IntCol
from openfisca_core.variables import Variable
from openfisca_core.formula_helpers import switch
from openfisca_core.tests import dummy_country
from openfisca_core.tests.dummy_country import Individus, Simulation


class choice(Variable):
    column = IntCol
    entity_class = Individus


class uses_multiplication(Variable):
    column = IntCol
    entity_class = Individus
    label = u'Variable with formula that uses multiplication'

    def function(self, simulation, period):
        choice = simulation.calculate('choice', period)
        result = (choice == 1) * 80 + (choice == 2) * 90
        return period, result


class uses_switch(Variable):
    column = IntCol
    entity_class = Individus
    label = u'Variable with formula that uses switch'

    def function(self, simulation, period):
        choice = simulation.calculate('choice', period)
        result = switch(
            choice,
            {
                1: 80,
                2: 90,
                },
            )
        return period, result


# TaxBenefitSystem instance declared after formulas
tax_benefit_system = dummy_country.DummyTaxBenefitSystem()
tax_benefit_system.add_variable_classes(choice, uses_multiplication, uses_switch)
simulation = Simulation(tax_benefit_system, attributes={
    'period': 2013,
    'input_variables': {
        # 'choice': [1, 1, 1, 2],
        'choice': np.random.randint(2, size=1000) + 1,
        },
    })


def test_switch():
    uses_switch = simulation.calculate('uses_switch')
    assert isinstance(uses_switch.value, np.ndarray)


def test_multiplication():
    uses_multiplication = simulation.calculate('uses_multiplication')
    assert isinstance(uses_multiplication.value, np.ndarray)


def test_compare_multiplication_and_switch():
    uses_multiplication = simulation.calculate('uses_multiplication')
    uses_switch = simulation.calculate('uses_switch')
    assert np.all((uses_switch == uses_multiplication).value)
