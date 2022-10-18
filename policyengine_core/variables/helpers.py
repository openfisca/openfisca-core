from __future__ import annotations

from typing import Optional

import sortedcontainers

from policyengine_core.periods import Period

from .. import variables


def get_annualized_variable(
    variable: variables.Variable, annualization_period: Optional[Period] = None
) -> variables.Variable:
    """
    Returns a clone of ``variable`` that is annualized for the period ``annualization_period``.
    When annualized, a variable's formula is only called for a January calculation, and the results for other months are assumed to be identical.
    """

    def make_annual_formula(original_formula, annualization_period=None):
        def annual_formula(population, period, parameters):
            if period.start.month != 1 and (
                annualization_period is None
                or annualization_period.contains(period)
            ):
                return population(variable.name, period.this_year.first_month)
            if original_formula.__code__.co_argcount == 2:
                return original_formula(population, period)
            return original_formula(population, period, parameters)

        return annual_formula

    new_variable = variable.clone()
    new_variable.formulas = sortedcontainers.sorteddict.SortedDict(
        {
            key: make_annual_formula(formula, annualization_period)
            for key, formula in variable.formulas.items()
        }
    )

    return new_variable


def get_neutralized_variable(variable):
    """
    Return a new neutralized variable (to be used by reforms).
    A neutralized variable always returns its default value, and does not cache anything.
    """
    result = variable.clone()
    result.is_neutralized = True
    result.label = (
        "[Neutralized]"
        if variable.label is None
        else "[Neutralized] {}".format(variable.label),
    )

    return result


def _partition(dict, predicate):
    true_dict = {}
    false_dict = {}

    for key, value in dict.items():
        if predicate(key, value):
            true_dict[key] = value
        else:
            false_dict[key] = value

    return true_dict, false_dict
