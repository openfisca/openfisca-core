"""Type guards to help type narrowing simulation parameters."""

from __future__ import annotations

from collections.abc import Iterable
from typing_extensions import TypeGuard

from .typing import (
    Axes,
    DatedVariable,
    FullySpecifiedEntities,
    ImplicitGroupEntities,
    Params,
    UndatedVariable,
    Variables,
)


def are_entities_fully_specified(
    params: Params,
    items: Iterable[str],
) -> TypeGuard[FullySpecifiedEntities]:
    """Check if the params contain fully specified entities.

    Args:
        params(Params): Simulation parameters.
        items(Iterable[str]): List of entities in plural form.

    Returns:
        bool: True if the params contain fully specified entities.

    Examples:
        >>> entities = {"persons", "households"}

        >>> params = {
        ...     "axes": [
        ...         [
        ...             {
        ...                 "count": 2,
        ...                 "max": 3000,
        ...                 "min": 0,
        ...                 "name": "rent",
        ...                 "period": "2018-11",
        ...             }
        ...         ]
        ...     ],
        ...     "households": {
        ...         "housea": {"parents": ["Alicia", "Javier"]},
        ...         "houseb": {"parents": ["Tom"]},
        ...     },
        ...     "persons": {"Alicia": {"salary": {"2018-11": 0}}, "Javier": {}, "Tom": {}},
        ... }

        >>> are_entities_fully_specified(params, entities)
        True

        >>> params = {"persons": {"Javier": {"salary": {"2018-11": [2000, 3000]}}}}

        >>> are_entities_fully_specified(params, entities)
        True

        >>> params = {"persons": {"Javier": {"salary": {"2018-11": 2000}}}}

        >>> are_entities_fully_specified(params, entities)
        True

        >>> params = {"household": {"parents": ["Javier"]}}

        >>> are_entities_fully_specified(params, entities)
        False

        >>> params = {"salary": {"2016-10": 12000}}

        >>> are_entities_fully_specified(params, entities)
        False

        >>> params = {"salary": 12000}

        >>> are_entities_fully_specified(params, entities)
        False

        >>> params = {}

        >>> are_entities_fully_specified(params, entities)
        False

    """
    if not params:
        return False

    return all(key in items for key in params if key != "axes")


def are_entities_short_form(
    params: Params,
    items: Iterable[str],
) -> TypeGuard[ImplicitGroupEntities]:
    """Check if the params contain short form entities.

    Args:
        params(Params): Simulation parameters.
        items(Iterable[str]): List of entities in singular form.

    Returns:
        bool: True if the params contain short form entities.

    Examples:
        >>> entities = {"person", "household"}

        >>> params = {
        ...     "persons": {"Javier": {"salary": {"2018-11": 2000}}},
        ...     "households": {"household": {"parents": ["Javier"]}},
        ...     "axes": [[{"count": 1, "max": 1, "min": 1, "name": "household"}]],
        ... }

        >>> are_entities_short_form(params, entities)
        False

        >>> params = {"persons": {"Javier": {"salary": {"2018-11": 2000}}}}

        >>> are_entities_short_form(params, entities)
        False

        >>> params = {
        ...     "persons": {"Javier": {"salary": {"2018-11": 2000}}},
        ...     "household": {"parents": ["Javier"]},
        ...     "axes": [[{"count": 1, "max": 1, "min": 1, "name": "household"}]],
        ... }

        >>> are_entities_short_form(params, entities)
        True

        >>> params = {
        ...     "household": {"parents": ["Javier"]},
        ...     "axes": [[{"count": 1, "max": 1, "min": 1, "name": "household"}]],
        ... }

        >>> are_entities_short_form(params, entities)
        True

        >>> params = {"household": {"parents": ["Javier"]}}

        >>> are_entities_short_form(params, entities)
        True

        >>> params = {"household": {"parents": "Javier"}}

        >>> are_entities_short_form(params, entities)
        True

        >>> params = {"salary": {"2016-10": 12000}}

        >>> are_entities_short_form(params, entities)
        False

        >>> params = {"salary": 12000}

        >>> are_entities_short_form(params, entities)
        False

        >>> params = {}

        >>> are_entities_short_form(params, entities)
        False

    """
    return bool(set(params).intersection(items))


def are_entities_specified(
    params: Params,
    items: Iterable[str],
) -> TypeGuard[Variables]:
    """Check if the params contains entities at all.

    Args:
        params(Params): Simulation parameters.
        items(Iterable[str]): List of variables.

    Returns:
        bool: True if the params does not contain variables at the root level.

    Examples:
        >>> variables = {"salary"}

        >>> params = {
        ...     "persons": {"Javier": {"salary": {"2018-11": 2000}}},
        ...     "households": {"household": {"parents": ["Javier"]}},
        ...     "axes": [[{"count": 1, "max": 1, "min": 1, "name": "household"}]],
        ... }

        >>> are_entities_specified(params, variables)
        True

        >>> params = {"persons": {"Javier": {"salary": {"2018-11": [2000, 3000]}}}}

        >>> are_entities_specified(params, variables)
        True

        >>> params = {"persons": {"Javier": {"salary": {"2018-11": 2000}}}}

        >>> are_entities_specified(params, variables)
        True

        >>> params = {"household": {"parents": ["Javier"]}}

        >>> are_entities_specified(params, variables)
        True

        >>> params = {"salary": {"2016-10": [12000, 13000]}}

        >>> are_entities_specified(params, variables)
        False

        >>> params = {"salary": {"2016-10": 12000}}

        >>> are_entities_specified(params, variables)
        False

        >>> params = {"salary": [12000, 13000]}

        >>> are_entities_specified(params, variables)
        False

        >>> params = {"salary": 12000}

        >>> are_entities_specified(params, variables)
        False

        >>> params = {}

        >>> are_entities_specified(params, variables)
        False

    """
    if not params:
        return False

    return not any(key in items for key in params)


def has_axes(params: Params) -> TypeGuard[Axes]:
    """Check if the params contains axes.

    Args:
        params(Params): Simulation parameters.

    Returns:
        bool: True if the params contain axes.

    Examples:
        >>> params = {
        ...     "persons": {"Javier": {"salary": {"2018-11": 2000}}},
        ...     "households": {"household": {"parents": ["Javier"]}},
        ...     "axes": [[{"count": 1, "max": 1, "min": 1, "name": "household"}]],
        ... }

        >>> has_axes(params)
        True

        >>> params = {"persons": {"Javier": {"salary": {"2018-11": [2000, 3000]}}}}

        >>> has_axes(params)
        False

    """
    return params.get("axes", None) is not None


def is_variable_dated(
    variable: DatedVariable | UndatedVariable,
) -> TypeGuard[DatedVariable]:
    """Check if the variable is dated.

    Args:
        variable(DatedVariable | UndatedVariable): A variable.

    Returns:
        bool: True if the variable is dated.

    Examples:
        >>> variable = {"2018-11": [2000, 3000]}

        >>> is_variable_dated(variable)
        True

        >>> variable = {"2018-11": 2000}

        >>> is_variable_dated(variable)
        True

        >>> variable = 2000

        >>> is_variable_dated(variable)
        False

    """
    return isinstance(variable, dict)
