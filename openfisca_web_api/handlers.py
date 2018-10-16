# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import

from copy import deepcopy

import dpath

from openfisca_core.simulations import Simulation
from openfisca_core.indexed_enums import Enum
from openfisca_core.commons import to_unicode


def calculate(tax_benefit_system, input_data):
    simulation = Simulation(tax_benefit_system = tax_benefit_system, simulation_json = input_data)

    requested_computations = dpath.util.search(input_data, '*/*/*/*', afilter = lambda t: t is None, yielded = True)
    computation_results = {}

    for computation in requested_computations:
        path = computation[0]
        entity_plural, entity_id, variable_name, period = path.split('/')
        variable = tax_benefit_system.get_variable(variable_name)
        result = simulation.calculate(variable_name, period)
        entity = simulation.get_entity(plural = entity_plural)
        entity_index = entity.ids.index(entity_id)

        if variable.value_type == Enum:
            entity_result = result.decode()[entity_index].name
        elif variable.value_type == float:
            entity_result = float(str(result[entity_index]))  # To turn the float32 into a regular float without adding confusing extra decimals. There must be a better way.
        elif variable.value_type == str:
            entity_result = to_unicode(result[entity_index])  # From bytes to unicode
        else:
            entity_result = result.tolist()[entity_index]

        dpath.util.new(computation_results, path, entity_result)

    dpath.merge(input_data, computation_results)

    return input_data


def trace(tax_benefit_system, input_data):
    simulation = Simulation(tax_benefit_system = tax_benefit_system, simulation_json = input_data, trace = True)

    requested_computations = dpath.util.search(input_data, '*/*/*/*', afilter = lambda t: t is None, yielded = True)
    for computation in requested_computations:
        path = computation[0]
        entity_plural, entity_id, variable_name, period = path.split('/')
        simulation.calculate(variable_name, period)

    trace = deepcopy(simulation.tracer.trace)
    for vector_key, vector_trace in trace.items():
        value = vector_trace['value'].tolist()
        if isinstance(value[0], Enum):
            value = [item.name for item in value]
        if isinstance(value[0], bytes):
            value = [to_unicode(item) for item in value]
        vector_trace['value'] = value

    return {
        "trace": trace,
        "entitiesDescription": {entity.plural: entity.ids for entity in simulation.entities.values()},
        "requestedCalculations": list(simulation.tracer.requested_calculations)
        }
