import logging
from typing import Any, Callable, Dict, List, Sequence, Type, TypeVar, Union

import numpy
import numpy as np
import pandas as pd
from numpy import logical_not as not_
from numpy import maximum as max_
from numpy import minimum as min_
from numpy import round as round_
from numpy import select, where

from policyengine_core.parameters.parameter_node import ParameterNode
from policyengine_core.periods.period_ import Period
from policyengine_core.populations.population import Population
from policyengine_core.types import ArrayLike, ArrayType
from policyengine_core.variables.variable import Variable

T = TypeVar("T")


def apply_thresholds(
    input: ArrayType[float],
    thresholds: ArrayLike[float],
    choices: ArrayLike[float],
) -> ArrayType[float]:
    """Makes a choice based on an input and thresholds.

    From a list of ``choices``, this function selects one of these values
    based on a list of inputs, depending on the value of each ``input`` within
    a list of ``thresholds``.

    Args:
        input: A list of inputs to make a choice from.
        thresholds: A list of thresholds to choose.
        choices: A list of the possible values to choose from.

    Returns:
        :obj:`numpy.ndarray` of :obj:`float`:
        A list of the values chosen.

    Raises:
        :exc:`AssertionError`: When the number of ``thresholds`` (t) and the
            number of choices (c) are not either t == c or t == c - 1.

    Examples:
        >>> input = numpy.array([4, 5, 6, 7, 8])
        >>> thresholds = [5, 7]
        >>> choices = [10, 15, 20]
        >>> apply_thresholds(input, thresholds, choices)
        array([10, 10, 15, 15, 20])

    """

    condlist: Sequence[ArrayType[bool]]
    condlist = [input <= threshold for threshold in thresholds]

    if len(condlist) == len(choices) - 1:
        # If a choice is provided for input > highest threshold, last condition
        # must be true to return it.
        condlist += [True]

    assert len(condlist) == len(choices), " ".join(
        [
            "'apply_thresholds' must be called with the same number of",
            "thresholds than choices, or one more choice.",
        ]
    )

    return numpy.select(condlist, choices)


def concat(this: ArrayLike[str], that: ArrayLike[str]) -> ArrayType[str]:
    """Concatenates the values of two arrays.

    Args:
        this: An array to concatenate.
        that: Another array to concatenate.

    Returns:
        :obj:`numpy.ndarray` of :obj:`float`:
        An array with the concatenated values.

    Examples:
        >>> this = ["this", "that"]
        >>> that = numpy.array([1, 2.5])
        >>> concat(this, that)
        array(['this1.0', 'that2.5']...)

    """

    if isinstance(this, numpy.ndarray) and not numpy.issubdtype(
        this.dtype, numpy.str_
    ):

        this = this.astype("str")

    if isinstance(that, numpy.ndarray) and not numpy.issubdtype(
        that.dtype, numpy.str_
    ):

        that = that.astype("str")

    return numpy.char.add(this, that)


def switch(
    conditions: ArrayType[Any],
    value_by_condition: Dict[float, T],
) -> ArrayType[T]:
    """Mimicks a switch statement.

    Given an array of conditions, returns an array of the same size,
    replacing each condition item with the matching given value.

    Args:
        conditions: An array of conditions.
        value_by_condition: Values to replace for each condition.

    Returns:
        :obj:`numpy.ndarray`:
        An array with the replaced values.

    Raises:
        :exc:`AssertionError`: When ``value_by_condition`` is empty.

    Examples:
        >>> conditions = numpy.array([1, 1, 1, 2])
        >>> value_by_condition = {1: 80, 2: 90}
        >>> switch(conditions, value_by_condition)
        array([80, 80, 80, 90])

    """

    assert (
        len(value_by_condition) > 0
    ), "'switch' must be called with at least one value."

    condlist = [
        conditions == condition for condition in value_by_condition.keys()
    ]

    return numpy.select(condlist, value_by_condition.values())


def for_each_variable(
    entity: Population,
    period: Period,
    variables: List[str],
    agg_func: str = "add",
    group_agg_func: str = "add",
    options: List[str] = None,
) -> ArrayLike:
    """Applies operations to lists of variables.

    Args:
        entity (Population): The entity population, as passed in formulas.
        period (Period): The period, as pass in formulas.
        variables (List[str]): A list of variable names.
        agg_func (str, optional): The operation to apply to combine variable results. Defaults to "add".
        group_agg_func (str, optional): The operation to apply to transform values to the target entity level. Defaults to "add".
        options (List[str], optional): Options to pass to the `entity(variable, period)` call. Defaults to None.

    Raises:
        ValueError: If any target variable is not at or below the target entity level.

    Returns:
        ArrayLike: The result of the operation.
    """
    result = None
    agg_func = dict(
        add=lambda x, y: x + y, multiply=lambda x, y: x * y, max=max_, min=min_
    )[agg_func]
    if not entity.entity.is_person:
        group_agg_func = dict(
            add=entity.sum, all=entity.all, max=entity.max, min=entity.min
        )[group_agg_func]
    for variable in variables:
        variable_entity = entity.entity.get_variable(variable).entity
        if variable_entity.key == entity.entity.key:
            values = entity(variable, period, options=options)
        elif variable_entity.is_person:
            values = group_agg_func(
                entity.members(variable, period, options=options)
            )
        elif entity.entity.is_person:
            raise ValueError(
                f"You requested to aggregate {variable} (defined for {variable_entity.plural}) to {entity.entity.plural}, but this is not yet implemented."
            )
        else:  # Group-to-group aggregation
            variable_population = entity.simulation.populations[
                variable_entity.key
            ]
            person_shares = variable_population.project(
                variable_population(variable, period)
            ) / variable_population.project(variable_population.nb_persons())
            values = entity.sum(person_shares)
        if result is None:
            result = values
        else:
            result = agg_func(result, values)
    return result


def add(
    entity: Population,
    period: Period,
    variables: List[str],
    options: List[str] = None,
):
    """Sums a list of variables.

    Args:
        entity (Population): The entity population, as passed in formulas.
        period (Period): The period, as pass in formulas.
        variables (List[str]): A list of variable names.
        options (List[str], optional): Options to pass to the `entity(variable, period)` call. Defaults to None.

    Raises:
        ValueError: If any target variable is not at or below the target entity level.

    Returns:
        ArrayLike: The result of the operation.
    """
    return for_each_variable(
        entity, period, variables, agg_func="add", options=options
    )


def aggr(entity, period, variables, options=None):
    """Sums a list of variables belonging to entity members.

    Args:
        entity (Population): The entity population, as passed in formulas.
        period (Period): The period, as pass in formulas.
        variables (List[str]): A list of variable names.
        options (List[str], optional): Options to pass to the `entity(variable, period)` call. Defaults to None.

    Raises:
        ValueError: If any target variable is not below the target entity level.

    Returns:
        ArrayLike: The result of the operation.
    """
    return for_each_variable(
        entity,
        period,
        variables,
        agg_func="add",
        group_agg_func="add",
        options=options,
    )


def and_(
    entity: Population,
    period: Period,
    variables: List[str],
    options: List[str] = None,
):
    """Performs a logical and operation on a list of variables.

    Args:
        entity (Population): The entity population, as passed in formulas.
        period (Period): The period, as pass in formulas.
        variables (List[str]): A list of variable names.
        options (List[str], optional): Options to pass to the `entity(variable, period)` call. Defaults to None.

    Raises:
        ValueError: If any target variable is not at the target entity level.

    Returns:
        ArrayLike: The result of the operation.
    """
    return for_each_variable(
        entity, period, variables, agg_func="multiply", options=options
    )


or_ = add
any_ = or_
multiply = and_

select = np.select


clip = np.clip
inf = np.inf

WEEKS_IN_YEAR = 52
MONTHS_IN_YEAR = 12


def amount_over(amount: ArrayLike, threshold: float) -> ArrayLike:
    """Calculates the amounts over a threshold.

    Args:
        amount (ArrayLike): The amount to calculate for.
        threshold_1 (float): The threshold.

    Returns:
        ArrayLike: The amounts over the threshold.
    """
    logging.debug(
        "amount_over(x, y) is deprecated, use max_(x - y, 0) instead."
    )
    return max_(0, amount - threshold)


def amount_between(
    amount: ArrayLike, threshold_1: float, threshold_2: float
) -> ArrayLike:
    """Calculates the amounts between two thresholds.

    Args:
        amount (ArrayLike): The amount to calculate for.
        threshold_1 (float): The lower threshold.
        threshold_2 (float): The upper threshold.

    Returns:
        ArrayLike: The amounts between the thresholds.
    """
    return clip(amount, threshold_1, threshold_2) - threshold_1


def random(entity, reset=True):
    if reset:
        np.random.seed(0)
    x = np.random.rand(entity.count)
    return x


def is_in(values: ArrayLike, *targets: list) -> ArrayLike:
    """Returns true if the value is in the list of targets.

    Args:
        values (ArrayLike): The values to test.

    Returns:
        ArrayLike: True if the value is in the list of targets.
    """
    if (len(targets) == 1) and isinstance(targets[0], list):
        targets = targets[0]
    return np.any([values == target for target in targets], axis=0)


def between(
    values: ArrayLike, lower: float, upper: float, inclusive: str = "both"
) -> ArrayLike:
    """Returns true if values are between lower and upper.

    Args:
        values (ArrayLike): The input array.
        lower (float): The lower bound.
        upper (float): The upper bound.
        inclusive (bool, optional): Whether to include or exclude the bounds. Defaults to True.

    Returns:
        ArrayLike: The resulting array.
    """
    return pd.Series(values).between(lower, upper, inclusive=inclusive)


def uprated(by: str = None, start_year: int = 2015) -> Callable:
    """Attaches a formula applying an uprating factor to input variables (going back as far as 2015).

    Args:
        by (str, optional): The name of the parameter (under parameters.uprating). Defaults to None (no uprating applied).

    Returns:
        Callable: A class decorator.
    """

    def uprater(variable: Type[Variable]) -> type:
        if hasattr(variable, f"formula_{start_year}"):
            return variable

        formula = variable.formula if hasattr(variable, "formula") else None

        variable.metadata = {
            "uprating": by,
        }

        def formula_start_year(entity, period, parameters):
            if by is None:
                return entity(variable.__name__, period.last_year)
            else:
                current_parameter = parameters(period)
                last_year_parameter = parameters(period.last_year)
                for name in by.split("."):
                    current_parameter = getattr(current_parameter, name)
                    last_year_parameter = getattr(last_year_parameter, name)
                uprating = current_parameter / last_year_parameter
                old = entity(variable.__name__, period.last_year)
                if (formula is not None) and (all(old) == 0):
                    # If no values have been inputted, don't uprate and
                    # instead use the previous formula on the current period.
                    return formula(entity, period, parameters)
                return uprating * old

        formula_start_year.__name__ = f"formula_{start_year}"
        setattr(variable, formula_start_year.__name__, formula_start_year)
        return variable

    return uprater


def carried_over(variable: type) -> type:
    return uprated()(variable)


def sum_of_variables(variables: Union[List[str], str]) -> Callable:
    """Returns a function that sums the values of a list of variables.

    Args:
        variables (Union[List[str], str]): A list of variable names.

    Returns:
        Callable: A function that sums the values of the variables.
    """

    def sum_of_variables(entity, period, parameters):
        if isinstance(variables, str):
            # A string parameter name is passed
            node = parameters(period)
            for name in variables.split("."):
                node = getattr(node, name)
            variable_names = node
        else:
            variable_names = variables
        return add(entity, period, variable_names)

    return sum_of_variables


any_of_variables = sum_of_variables


def index_(
    into: ParameterNode,
    indices: Union[ArrayLike, List[ArrayLike]],
    where: ArrayLike,
    fill: float = 0,
) -> ArrayLike:
    """Indexes into a object, but only when a condition is true. This improves
    performance over `np.where`, which will index all values and then filter the result.

    Args:
        into (Parameter): The parameter to index into.
        indices (Union[ArrayLike, List[ArrayLike]]): The full, un-filtered index array. Can be a list of arrays
            for sequential indexing.
        where (ArrayLike): A filter for indexing.
        fill (float, optional): The value to fill where `index_where` is False. Defaults to 0.

    Returns:
        ArrayLike: The indexed result.
    """
    if where.sum() == 0:
        return np.ones(where.shape) * fill

    if isinstance(indices, list):
        result = np.empty_like(indices[0])
        intermediate_result = into
        for i in range(len(indices)):
            intermediate_result = intermediate_result[indices[i][where]]
        result[where] = intermediate_result
    else:
        result = np.empty_like(indices)
        result[where] = into[indices[where]]
    result[~where] = fill
    return result.astype(float)
