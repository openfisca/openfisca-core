import dpath

from openfisca_core import periods
from openfisca_core.errors import PeriodMismatchError, SituationParsingError
from openfisca_core.indexed_enums import Enum
from openfisca_core.simulations import SimulationBuilder


def _calculate_requested(simulation, path: str, variable_name: str, period: str):
    """Calculate a requested variable, raising a period mismatch as a SituationParsingError."""
    try:
        return simulation.calculate(variable_name, period)
    except PeriodMismatchError as e:
        # Raised from inside a formula: a country package bug, keep the 500.
        if e.variable_name != variable_name or e.period != periods.period(period):
            raise
        raise SituationParsingError(path.split("/"), e.message) from e


def calculate(tax_benefit_system, input_data: dict) -> dict:
    """Returns the input_data where the None values are replaced by the calculated values."""
    simulation = SimulationBuilder().build_from_entities(tax_benefit_system, input_data)
    requested_computations = dpath.search(
        input_data,
        "*/*/*/*",
        afilter=lambda t: t is None,
        yielded=True,
    )
    computation_results: dict = {}
    for computation in requested_computations:
        path = computation[
            0
        ]  # format: entity_plural/entity_instance_id/openfisca_variable_name/period
        entity_plural, entity_id, variable_name, period = path.split("/")
        variable = tax_benefit_system.get_variable(variable_name)
        result = _calculate_requested(simulation, path, variable_name, period)
        population = simulation.get_population(entity_plural)
        entity_index = population.get_index(entity_id)

        if variable.value_type == Enum:
            entity_result = result.decode()[entity_index].name
        elif variable.value_type == float:
            entity_result = float(
                str(result[entity_index]),
            )  # To turn the float32 into a regular float without adding confusing extra decimals. There must be a better way.
        elif variable.value_type == str:
            entity_result = str(result[entity_index])
        else:
            entity_result = result.tolist()[entity_index]
        # Don't use dpath.new, because there is a problem with dpath>=2.0
        # when we have a key that is numeric, like the year.
        # See https://github.com/dpath-maintainers/dpath-python/issues/160
        if computation_results == {}:
            computation_results = {
                entity_plural: {entity_id: {variable_name: {period: entity_result}}},
            }
        elif entity_plural in computation_results:
            if entity_id in computation_results[entity_plural]:
                if variable_name in computation_results[entity_plural][entity_id]:
                    computation_results[entity_plural][entity_id][variable_name][
                        period
                    ] = entity_result
                else:
                    computation_results[entity_plural][entity_id][variable_name] = {
                        period: entity_result,
                    }
            else:
                computation_results[entity_plural][entity_id] = {
                    variable_name: {period: entity_result},
                }
        else:
            computation_results[entity_plural] = {
                entity_id: {variable_name: {period: entity_result}},
            }
    dpath.merge(input_data, computation_results)

    return input_data


def trace(tax_benefit_system, input_data):
    simulation = SimulationBuilder().build_from_entities(tax_benefit_system, input_data)
    simulation.trace = True

    requested_calculations = []
    requested_computations = dpath.search(
        input_data,
        "*/*/*/*",
        afilter=lambda t: t is None,
        yielded=True,
    )
    for computation in requested_computations:
        path = computation[0]
        _entity_plural, _entity_id, variable_name, period = path.split("/")
        requested_calculations.append(f"{variable_name}<{period!s}>")
        _calculate_requested(simulation, path, variable_name, period)

    trace = simulation.tracer.get_serialized_flat_trace()

    return {
        "trace": trace,
        "entitiesDescription": simulation.describe_entities(),
        "requestedCalculations": requested_calculations,
    }
