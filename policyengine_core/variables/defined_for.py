from typing import Any, Callable

import numpy as np
from numpy.typing import ArrayLike
from openfisca_core.entities import Entity
from openfisca_core.populations import GroupPopulation, Population
from openfisca_core.projectors import EntityToPersonProjector, Projector
from openfisca_core.variables import Variable


class CallableSubset:
    def __init__(
        self, population: Population, callable: Callable, mask: ArrayLike
    ):
        self.population = population
        self.callable = callable
        self.mask = mask

    def __call__(self, array: ArrayLike = None, *args, **kwargs):
        if array is None:
            return self.callable(*args, **kwargs)[self.mask]
        # Here, we're in e.g. household.sum(...).
        # The OpenFisca Population objects can map from e.g. people to households,
        # but they use primary/foreign key maps for the entire population. So,
        # for a subset of the population, we need to go back to the full population
        # (filling in with zeroes), use OpenFisca's mapping, then re-filter.
        if len(array) == self.population.members.count:
            return self.callable(array, *args, **kwargs)[self.mask]
        decompressed_size = self.population.members.count
        if len(self.mask) != decompressed_size:
            mask = self.population.project(self.mask)
        else:
            mask = self.mask
        decompressed_array = np.zeros((decompressed_size,))
        decompressed_array[mask] = array
        return self.callable(decompressed_array, *args, **kwargs)[self.mask]


class PopulationSubset:
    def __init__(self, population: Population, mask: ArrayLike):
        self.population = population
        self.mask = mask

    def __call__(self, *args, **kwargs):
        return self.population(*args, **kwargs)[self.mask]

    def __getattribute__(self, attribute):
        if attribute in ("population", "mask"):
            return object.__getattribute__(self, attribute)
        original_result = getattr(self.population, attribute)
        if isinstance(original_result, EntityToPersonProjector):
            # e.g. person.household
            return PopulationSubset(original_result, self.mask)
        elif attribute in (
            "sum",
            "min",
            "max",
            "nb_persons",
            "any",
            "all",
            "value_from_first_person",
        ):
            return CallableSubset(self.population, original_result, self.mask)
        return original_result


def make_partially_executed_formula(
    formula: Callable,
    mask: ArrayLike,
    default_value: Any = 0,
    value_type: type = float,
) -> Callable:
    # Edge cases that need to be covered:
    # * entity(variable, period)
    # * entity.members(variable, period)
    # * entity.parent_entity(variable, period)

    def partially_executed_formula(entity, period, parameters):
        if isinstance(mask, str):
            mask_entity = entity.simulation.tax_benefit_system.variables[
                mask
            ].entity.key
            if entity.entity.key != mask_entity:
                mask_values = getattr(entity, mask_entity)(mask, period)
            else:
                mask_values = entity(mask, period)
        else:
            mask_values = mask

        result = np.ones_like(mask_values, dtype=value_type) * default_value

        if not mask_values.any():
            return result

        subset_entity = PopulationSubset(entity, mask_values)

        formula_result = formula(subset_entity, period, parameters)
        formula_result = np.array(formula_result)

        result[mask_values] = formula_result

        entity = subset_entity.population

        return result

    return partially_executed_formula
