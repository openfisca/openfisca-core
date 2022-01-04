# -*- coding: utf-8 -*-

import dpath.util
import copy
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_core.indexed_enums import Enum


def calculate(tax_benefit_system, input_data):
    simulation = SimulationBuilder().build_from_entities(tax_benefit_system, input_data)
# BCO: 
    requested_computations = dpath.util.search(input_data, '*/*/*/*', afilter = lambda t: t is None, yielded = True)
    computation_results = {}
    #computation_results = copy.deepcopy(input_data)

    for computation in requested_computations:
        path = computation[0]
        entity_plural, entity_id, variable_name, period = path.split('/')
        #if computation_results == {}:
        #    computation_results = {entity_plural: {entity_id:{variable_name:None}}}
        # BCO 'households/_/housing_tax/2017'
        # variable_name =  'housing_tax'
        # persons/Alicia/disposable_income/2017-01
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

    dpath.util.merge(input_data, computation_results)

    return input_data


def trace(tax_benefit_system, input_data):
    simulation = SimulationBuilder().build_from_entities(tax_benefit_system, input_data)
    simulation.trace = True

    requested_calculations = []
    requested_computations = dpath.util.search(input_data, '*/*/*/*', afilter = lambda t: t is None, yielded = True)
    for computation in requested_computations:
        path = computation[0]
        entity_plural, entity_id, variable_name, period = path.split('/')
        requested_calculations.append(f"{variable_name}<{str(period)}>")
        simulation.calculate(variable_name, period)

    trace = simulation.tracer.get_serialized_flat_trace()

    return {
        "trace": trace,
        "entitiesDescription": simulation.describe_entities(),
        "requestedCalculations": requested_calculations
        }
