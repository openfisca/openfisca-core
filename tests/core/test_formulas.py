# -*- coding: utf-8 -*-

import numpy as np

from openfisca_core.periods import MONTH
from openfisca_core.variables import Variable
from openfisca_core.formula_helpers import switch
from openfisca_country_template.entities import Person

from pytest import fixture, approx


class choice(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH


class uses_multiplication(Variable):
    value_type = int
    entity = Person
    label = 'Variable with formula that uses multiplication'
    definition_period = MONTH

    def formula(person, period):
        choice = person('choice', period)
        result = (choice == 1) * 80 + (choice == 2) * 90
        return result


class returns_scalar(Variable):
    value_type = int
    entity = Person
    label = 'Variable with formula that returns a scalar value'
    definition_period = MONTH

    def formula(person, period):
        return 666


class uses_switch(Variable):
    value_type = int
    entity = Person
    label = 'Variable with formula that uses switch'
    definition_period = MONTH

    def formula(person, period):
        choice = person('choice', period)
        result = switch(
            choice,
            {
                1: 80,
                2: 90,
                },
            )
        return result


@fixture
def our_tbs(tax_benefit_system):
    tax_benefit_system.add_variables(choice, uses_multiplication, uses_switch, returns_scalar)
    return tax_benefit_system


@fixture
def month():
    return '2013-01'


@fixture
def simulation(our_tbs, simulation_builder, month):
    simulation_builder.default_period = month
    simulation = simulation_builder.build_from_variables(
        our_tbs,
        {'choice': np.random.randint(2, size = 1000) + 1}
        )
    simulation.debug = True
    return simulation


def test_switch(simulation, month):
    uses_switch = simulation.calculate('uses_switch', period = month)
    assert isinstance(uses_switch, np.ndarray)


def test_multiplication(simulation, month):
    uses_multiplication = simulation.calculate('uses_multiplication', period = month)
    assert isinstance(uses_multiplication, np.ndarray)


def test_broadcast_scalar(simulation, month):
    array_value = simulation.calculate('returns_scalar', period = month)
    assert isinstance(array_value, np.ndarray)
    assert array_value == approx(np.repeat(666, 1000))


def test_compare_multiplication_and_switch(simulation, month):
    uses_multiplication = simulation.calculate('uses_multiplication', period = month)
    uses_switch = simulation.calculate('uses_switch', period = month)
    assert np.all(uses_switch == uses_multiplication)
