# -*- coding: utf-8 -*-


from __future__ import unicode_literals, print_function, division, absolute_import

import shutil
import tempfile

import numpy as np

from openfisca_core.variables import Variable
from openfisca_core.periods import MONTH
from openfisca_country_template import CountryTaxBenefitSystem
from openfisca_country_template.entities import Person


class input(Variable):
    value_type = int
    entity = Person
    label = "Input variable"
    definition_period = MONTH


class intermediate(Variable):
    value_type = int
    entity = Person
    label = "Intermediate value"
    definition_period = MONTH

    def formula(person, period):
        return person('input', period)


class output(Variable):
    value_type = int
    entity = Person
    label = 'Output variable'
    definition_period = MONTH

    def formula(person, period):
        return person('intermediate', period)


def create_filled_tax_benefit_system():
    tax_benefit_system = CountryTaxBenefitSystem()
    tax_benefit_system.add_variables(input, intermediate, output)

    return tax_benefit_system


# TaxBenefitSystem instance declared after formulas


tax_benefit_system = create_filled_tax_benefit_system()


month = '2018-08'
scenario = tax_benefit_system.new_scenario().init_from_attributes(
    period = month,
    input_variables = {
        'input': 1,
        },
    )


def test_dump_restore_same_simulation():
    simulation = scenario.new_simulation()
    simulation.calculate('output', period = month)
    assert(simulation.get_holder('output').get_array(month) == simulation.get_holder('input').get_array(month))

    simulation.dump()

    assert(simulation.get_holder('output').get_array(month) == simulation.get_holder('input').get_array(month))

    simulation.get_holder('output').set_input(month, [2])

    next_month = '2018-09'
    next_value = 3
    simulation.get_holder('input').set_input(next_month, [next_value])
    simulation.calculate('output', period = next_month)
    assert(simulation.get_holder('output').get_array(next_month) == simulation.get_holder('input').get_array(next_month))

    simulation.restore()

    assert(simulation.get_holder('output').get_array(month) == simulation.get_holder('input').get_array(month))

    assert(simulation.get_holder('input').get_array(next_month) is None)
    assert(simulation.get_holder('intermediate').get_array(next_month) is None)
    assert(simulation.get_holder('output').get_array(next_month) is None)


def test_dump_restore_different_simulations():
    data_storage_dir = tempfile.mkdtemp(prefix = "openfisca_")

    simulation1 = scenario.new_simulation(data_storage_dir = data_storage_dir)
    simulation1.calculate('output', period = month, extra_params = [-1, -2])

    simulation1.dump()

    # New simulation with the same storage directory
    simulation2 = scenario.new_simulation(data_storage_dir = data_storage_dir)

    simulation2.restore()

    assert(simulation2.get_holder('input').get_array(month) == np.asarray([1]))
    assert(simulation2.get_holder('intermediate').get_array(month) == np.asarray([1]))
    assert(simulation2.get_holder('output').get_array(month, extra_params = [-1, -2]) == np.asarray([1]))

    shutil.rmtree(data_storage_dir)
