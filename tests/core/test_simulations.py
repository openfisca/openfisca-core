# -*- coding: utf-8 -*-

def test_calculate_full_tracer(tax_benefit_system, simulation_builder):
    simulation = simulation_builder.build_default_simulation(tax_benefit_system)
    simulation.trace = True
    simulation.calculate('income_tax', '2017-01')

    income_tax_node = simulation.tracer.trees[0]
    assert income_tax_node.name == 'income_tax'
    assert str(income_tax_node.period) == '2017-01'
    assert income_tax_node.value == 0

    salary_node = income_tax_node.children[0]
    assert salary_node.name == 'salary'
    assert str(salary_node.period) == '2017-01'
    assert salary_node.parameters == []

    assert len(income_tax_node.parameters) == 1
    assert income_tax_node.parameters[0].name == 'taxes.income_tax_rate'
    assert income_tax_node.parameters[0].period == '2017-01-01'
    assert income_tax_node.parameters[0].value == 0.15


def test_get_entity_not_found(tax_benefit_system, simulation_builder):
    simulation = simulation_builder.build_default_simulation(tax_benefit_system)
    assert simulation.get_entity(plural = "no_such_entities") is None


def test_clone(tax_benefit_system, simulation_builder):
    simulation = simulation_builder.build_from_entities(tax_benefit_system,
            {
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

    for entity_id, entity in simulation.populations.items():
        assert entity != simulation_clone.populations[entity_id]

    assert simulation.persons != simulation_clone.persons

    salary_holder = simulation.person.get_holder('salary')
    salary_holder_clone = simulation_clone.person.get_holder('salary')

    assert salary_holder != salary_holder_clone
    assert salary_holder_clone.simulation == simulation_clone
    assert salary_holder_clone.population == simulation_clone.persons


def test_get_memory_usage(tax_benefit_system, simulation_builder, single):
    simulation = simulation_builder.build_from_entities(tax_benefit_system, single)
    simulation.calculate('disposable_income', '2017-01')
    memory_usage = simulation.get_memory_usage(variables = ['salary'])
    assert(memory_usage['total_nb_bytes'] > 0)
    assert(len(memory_usage['by_variable']) == 1)
