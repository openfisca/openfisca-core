# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
import os

from openfisca_core.simulations import Simulation
from openfisca_core.variables import Variable
from openfisca_core.parameters import ParameterNode
from openfisca_core.periods import MONTH

from openfisca_country_template.situation_examples import single
from openfisca_country_template.entities import Person

from .test_countries import tax_benefit_system


class zone(Variable):
    value_type = str
    entity = Person
    definition_period = MONTH
    label = "Variable for fancy indexing inputs"


class fancy_indexing(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = "Variable using fancy indexing"

    def formula(person, period, parameters):
        zone = person('zone', period)
        return parameters(period).rate.single.owner[zone]


LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))
fancy_indexing_directory = os.path.join(LOCAL_DIR, 'parameters_fancy_indexing')
parameters = ParameterNode(directory_path = fancy_indexing_directory)
tax_benefit_system.parameters.merge(parameters)

tax_benefit_system.add_variable(fancy_indexing)
tax_benefit_system.add_variable(zone)

scenario = tax_benefit_system.new_scenario().init_from_attributes(
    period='2017-01', input_variables={'zone': ['z1', 'z1', 'z1']}
    )


def test_calculate_with_trace():
    simulation = scenario.new_simulation(trace=True)
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

    # Tracing of fancy indexed parameters is not yet supported
    simulation.calculate('fancy_indexing', '2017-01')
    fancy_indexing_trace = simulation.tracer.trace['fancy_indexing<2017-01>']
    assert 'rate.single.owner.z1<2017-01-01>' not in fancy_indexing_trace['parameters']
    assert 'rate.single.owner.z2<2017-01-01>' not in fancy_indexing_trace['parameters']


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
        assert entity.entities_json == simulation_clone.entities[entity_id].entities_json

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
