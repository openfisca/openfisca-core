# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import

from openfisca_core.simulations import Simulation

from openfisca_country_template.situation_examples import single

from .test_countries import tax_benefit_system


scenario = tax_benefit_system.new_scenario().init_from_attributes(period = '2017-01')


def test_calculate_with_trace():
    simulation = scenario.new_simulation(trace = True)
    simulation.calculate('income_tax', '2017-01')

    salary_trace = simulation.tracer.trace['salary<2017-01>']
    assert salary_trace['parameters'] == {}

    income_tax_trace = simulation.tracer.trace['income_tax<2017-01>']
    assert income_tax_trace['parameters']['taxes.income_tax_rate<2017-01-01>'] == 0.15

    # Trace parameters called with indirect access
    simulation.calculate('housing_tax', '2017')
    housing_tax_trace = simulation.tracer.trace['housing_tax<2017>']
    assert 'taxes.housing_tax<2017-01-01>' not in housing_tax_trace['parameters']
    assert housing_tax_trace['parameters']['taxes.housing_tax.rate<2017-01-01>'] == 10
    assert housing_tax_trace['parameters']['taxes.housing_tax.minimal_amount<2017-01-01>'] == 200


def test_clone():
    simulation = Simulation(
        tax_benefit_system = tax_benefit_system,
        simulation_json = {
            "persons": {
                "bill": {"salary": {"2017-01": 3000}},
                },
            "households": {
                "household": {
                    "parents": ["bill"]
                    }
                }
            })

    simulation_clone = simulation.clone()
    assert simulation != simulation_clone

    for entity_id, entity in simulation.entities.items():
        assert entity != simulation_clone.entities[entity_id]

    assert simulation.persons != simulation_clone.persons

    salary_holder = simulation.person.get_holder('salary')
    salary_holder_clone = simulation_clone.person.get_holder('salary')

    assert salary_holder != salary_holder_clone
    assert salary_holder_clone.simulation == simulation_clone
    assert salary_holder_clone.entity == simulation_clone.person


def test_get_memory_usage():
    simulation = Simulation(tax_benefit_system = tax_benefit_system, simulation_json = single)
    simulation.calculate('disposable_income', '2017-01')
    memory_usage = simulation.get_memory_usage(variables = ['salary'])
    assert(memory_usage['total_nb_bytes'] > 0)
    assert(len(memory_usage['by_variable']) == 1)
