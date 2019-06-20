# -*- coding: utf-8 -*-


from copy import deepcopy
from collections import ChainMap
from typing import Dict


import dpath

from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_core.indexed_enums import Enum, EnumArray



def calculate(tax_benefit_system, input_data):
    simulation = SimulationBuilder().build_from_entities(tax_benefit_system, input_data)

    requested_computations = dpath.util.search(input_data, '*/*/*/*', afilter = lambda t: t is None, yielded = True)
    computation_results = {}

    for computation in requested_computations:
        path = computation[0]
        entity_plural, entity_id, variable_name, period = path.split('/')
        variable = tax_benefit_system.get_variable(variable_name)
        result = simulation.calculate(variable_name, period)
        population = simulation.get_population(entity_plural)
        entity_index = population.get_index(entity_id)

        if variable.value_type == Enum:
            entity_result = result.decode()[entity_index].name
        elif variable.value_type == float:
            entity_result = float(str(result[entity_index]))  # To turn the float32 into a regular float without adding confusing extra decimals. There must be a better way.
        elif variable.value_type == str:
            entity_result = str(result[entity_index])
        else:
            entity_result = result.tolist()[entity_index]

        dpath.util.new(computation_results, path, entity_result)

    dpath.merge(input_data, computation_results)

    return input_data


def get_flat_trace(node) -> Dict[str, Dict]:
    key = f"{node['name']}<{node['period']}>"
    node_trace = {
        key: {
        'dependencies': [
            f"{child['name']}<{child['period']}>"
            for child in node['children']
        ],
        'value': node['value']
        }}
    child_traces = [
        get_flat_trace(child)
        for child in node['children']
    ]

    return dict(ChainMap(node_trace, *child_traces))



def trace(tax_benefit_system, input_data):
    simulation = SimulationBuilder().build_from_entities(tax_benefit_system, input_data)
    simulation.trace = True

    requested_computations = dpath.util.search(input_data, '*/*/*/*', afilter = lambda t: t is None, yielded = True)
    for computation in requested_computations:
        path = computation[0]
        entity_plural, entity_id, variable_name, period = path.split('/')
        simulation.calculate(variable_name, period)

    trace = get_flat_trace(simulation.tracer.trees)
    requested_calculations = {}

    # for _vector_key, vector_trace in trace.items():
    #     value = vector_trace['value'].tolist()
    #     if isinstance(vector_trace['value'], EnumArray):
    #         value = [item.name for item in vector_trace['value'].decode()]
    #     if isinstance(value[0], bytes):
    #         value = [str(item) for item in value]
    #     vector_trace['value'] = value

    return {
        "trace": trace,
        "entitiesDescription": simulation.describe_entities(),
        "requestedCalculations": requested_calculations
        }
