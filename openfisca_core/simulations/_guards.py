"""Type guards to help type narrowing simulation parameters.

Every calculation in a simulation requires an entity, a variable, a period, and
a value. However, the way users can specify these elements can vary. This
module provides type guards to help narrow down the type of simulation
parameters, to help both readability and maintainability.

For example, the following is a perfectly valid, albeit complex, way to specify
a simulation's parameters::

    .. code-block:: python

        params = {
            "axes": [
                [
                    {
                        "count": 2,
                        "max": 3000,
                        "min": 0,
                        "name":
                        "rent",
                        "period": "2018-11"
                    }
                ]
            ],
            "households": {
                "housea": {
                    "parents": ["Alicia", "Javier"]
                },
                "houseb": {
                    "parents": ["Tom"]
                },
            },
            "persons": {
                "Alicia": {
                    "salary": {
                        "2018-11": 0
                    }
                },
                "Javier": {},
                "Tom": {}
            },
        }

"""

from __future__ import annotations

from collections.abc import Iterable
from typing_extensions import TypeGuard

import pydantic

from openfisca_core import periods

from .types import (
    Axes,
    Axis,
    DatedValue,
    FullySpecifiedEntities,
    ImplicitGroupEntities,
    Params,
    ParamsWithAxes,
    PureValue,
    Roles,
    Variables,
)

#: Pydantic type adapter to extract information from axes.
adapter = pydantic.TypeAdapter(Axis)

#: Field schema for axes.
axis_schema = adapter.core_schema

#: Required fields.
axis_required = [
    key for key, value in axis_schema["fields"].items() if value["required"]
]


def is_a_pure_value(
    value: object,
) -> TypeGuard[PureValue]:
    """Check if an input value is undated.

    The most atomic elements of a simulation are pure values. They can be
    either scalars or vectors. For example::

        .. code-block:: python

            1.5
            True
            [1000, 2000]

    Args:
        value(object): A value.

    Returns:
        bool: True if the value is undated.

    Examples:
        >>> value = 2000
        >>> is_a_pure_value(value)
        True

        >>> value = [2000, 3000]
        >>> is_a_pure_value(value)
        True

        >>> value = {"2000": 2000}
        >>> is_a_pure_value(value)
        False

        >>> value = {"2018-W01": [2000, 3000]}
        >>> is_a_pure_value(value)
        False

        >>> value = {"123": 123}
        >>> is_a_pure_value(value)
        False

    """

    return not isinstance(value, dict)


def is_a_dated_value(
    value: object,
) -> TypeGuard[DatedValue]:
    """Check if an input value is dated.

    Pure values are associated with the simulation's period behind the scenes.
    However, some calculations require different values for variables for
    different periods. In such a case, users can specify dated values::

        .. code-block:: python

            {"2018-01": 2000}
            {"2018-W01": [2000, 3000]}
            {"2018-W01-1": 2000, "2018-W01-2": [3000, 4000]}

    Args:
        value(object): A value.

    Returns:
        bool: True if the value is dated.

    Examples:
        >>> value = 2000
        >>> is_a_dated_value(value)
        False

        >>> value = [2000, 3000]
        >>> is_a_dated_value(value)
        False

        >>> value = {"2000": 2000}
        >>> is_a_dated_value(value)
        True

        >>> value = {"2018-W01": [2000, 3000]}
        >>> is_a_dated_value(value)
        True

        >>> value = {"123": 123}
        >>> is_a_dated_value(value)
        False

    """

    if not isinstance(value, dict):
        return False

    try:
        return all(periods.period(key) for key in value.keys())

    except ValueError:
        return False


def are_variables(
    value: object,
) -> TypeGuard[Variables]:
    """Check if an input value is a map of variables.

    In a simulation, every value has to be associated with a variable. As with
    values, variables cannot be inferred from the context. Users have to
    explicitly specify them. For example::

        .. code-block:: python

            {"salary": 2000}
            {"taxes": {"2018-W01-1": [123, 234]}}
            {"taxes": {"2018-W01-1": [123, 234]}, "salary": 123}

    Args:
        value(object): A value.

    Returns:
        bool: True if the value is a map of variables.

    Examples:
        >>> value = 2000
        >>> are_variables(value)
        False

        >>> value = [2000, 3000]
        >>> are_variables(value)
        False

        >>> value = {"2000": 2000}
        >>> are_variables(value)
        False

        >>> value = {"2018-W01": [2000, 3000]}
        >>> are_variables(value)
        False

        >>> value = {"salary": 123}
        >>> are_variables(value)
        True

        >>> value = {"taxes": {"2018-W01-1": [123, 234]}}
        >>> are_variables(value)
        True

        >>> value = {"taxes": {"2018-W01-1": [123, 234]}, "salary": 123}
        >>> are_variables(value)
        True

    """

    if is_a_pure_value(value):
        return False

    if is_a_dated_value(value):
        return False

    return True


def are_roles(
    value: object,
) -> TypeGuard[Roles]:
    """Check if an input value is a map of roles.

    In a simulation, there are cases where we need to calculate things for
    group entities, for example, households. In such cases, some calculations
    require that we specify certain roles. For example::

        .. code-block:: python

            {"principal": "Alicia"}
            {"parents": ["Alicia", "Javier"]}

    Args:
        value(object): A value.

    Returns:
        bool: True if the value is a map of roles.

    Examples:
        >>> value = "parent"
        >>> are_roles(value)
        False

        >>> value = ["dad", "son"]
        >>> are_roles(value)
        False

        >>> value = {"2018-W01": [2000, 3000]}
        >>> are_roles(value)
        False

        >>> value = {"salary": 123}
        >>> are_roles(value)
        False

        >>> value = {"principal": "Alicia"}
        >>> are_roles(value)
        True

        >>> value = {"kids": ["Alicia", "Javier"]}
        >>> are_roles(value)
        True

        >>> value = {"principal": "Alicia", "kids": ["Tom"]}
        >>> are_roles(value)
        True

    """

    if not isinstance(value, dict):
        return False

    for role_key, role_id in value.items():
        if not isinstance(role_key, str):
            return False

        if not isinstance(role_id, (Iterable, str)):
            return False

        if isinstance(role_id, Iterable):
            for role in role_id:
                if not isinstance(role, str):
                    return False

    return True


def are_axes(value: object) -> TypeGuard[Axes]:
    """Check if the given params are axes.

    Axis expansion is a feature that allows users to parametrise some
    dimensions in order to create and to evaluate a range of values for others.

    Args:
        value(object): Simulation parameters.

    Returns:
        bool: True if the params are axes.

    Examples:
        >>> value = {
        ...     "persons": {"Javier": { "salary": { "2018-11": 2000}}},
        ...     "households": {"household": {"parents": ["Javier"]}},
        ...     "axes": [[{"count": 1, "max": 1, "min": 1, "name": "household"}]]
        ... }
        >>> are_axes(value)
        False

        >>> value = {
        ...     "axes": [[{"count": 1, "max": 1, "min": 1, "name": "household"}]]
        ... }
        >>> are_axes(value)
        False

        >>> value = [[{"a": 1, "b": 1, "c": 1}]]
        >>> are_axes(value)
        False

        >>> value = [[{"count": 1, "max": 1, "min": 1, "name": "household"}]]
        >>> are_axes(value)
        True

    """

    if not isinstance(value, (list, tuple)):
        return False

    (inner,) = value

    if not isinstance(inner, (list, tuple)):
        return False

    return all(key in axis_required for key in inner[0].keys())


def are_entities_specified(
    params: Params, items: Iterable[str]
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
        ...     "persons": {"Javier": { "salary": { "2018-11": 2000}}},
        ...     "households": {"household": {"parents": ["Javier"]}},
        ...     "axes": [[{"count": 1, "max": 1, "min": 1, "name": "household"}]]
        ... }

        >>> are_entities_specified(params, variables)
        True

        >>> params = {
        ...     "persons": {"Javier": {"salary": {"2018-11": [2000, 3000]}}}
        ... }

        >>> are_entities_specified(params, variables)
        True

        >>> params = {
        ...     "persons": {"Javier": {"salary": {"2018-11": 2000}}}
        ... }

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

    return not any(key in items for key in params.keys())


def are_entities_short_form(
    params: Params, items: Iterable[str]
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
        ...     "persons": {"Javier": { "salary": { "2018-11": 2000}}},
        ...     "households": {"household": {"parents": ["Javier"]}},
        ...     "axes": [[{"count": 1, "max": 1, "min": 1, "name": "household"}]]
        ... }

        >>> are_entities_short_form(params, entities)
        False

        >>> params = {
        ...     "persons": {"Javier": {"salary": {"2018-11": 2000}}}
        ... }

        >>> are_entities_short_form(params, entities)
        False

        >>> params = {
        ...     "persons": {"Javier": { "salary": { "2018-11": 2000}}},
        ...     "household": {"parents": ["Javier"]},
        ...     "axes": [[{"count": 1, "max": 1, "min": 1, "name": "household"}]]
        ... }

        >>> are_entities_short_form(params, entities)
        True

        >>> params = {
        ...     "household": {"parents": ["Javier"]},
        ...     "axes": [[{"count": 1, "max": 1, "min": 1, "name": "household"}]]
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

    return not not set(params).intersection(items)


def are_entities_fully_specified(
    params: Params, items: Iterable[str]
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
        ...         [{"count": 2, "max": 3000, "min": 0, "name": "rent", "period": "2018-11"}]
        ...     ],
        ...     "households": {
        ...         "housea": {"parents": ["Alicia", "Javier"]},
        ...         "houseb": {"parents": ["Tom"]},
        ...    },
        ...     "persons": {"Alicia": {"salary": {"2018-11": 0}}, "Javier": {}, "Tom": {}},
        ... }

        >>> are_entities_fully_specified(params, entities)
        True

        >>> params = {
        ...     "persons": {"Javier": {"salary": {"2018-11": [2000, 3000]}}}
        ... }

        >>> are_entities_fully_specified(params, entities)
        True

        >>> params = {
        ...     "persons": {"Javier": {"salary": {"2018-11": 2000}}}
        ... }

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

    return all(key in items for key in params.keys() if key != "axes")


def has_axes(value: object) -> TypeGuard[ParamsWithAxes]:
    """Check if the params contains axes.

    Args:
        value(object): Simulation parameters.

    Returns:
        bool: True if the params contain axes.

    Examples:
        >>> value = {
        ...     "persons": {"Javier": { "salary": { "2018-11": 2000}}},
        ...     "households": {"household": {"parents": ["Javier"]}},
        ...     "axes": [[{"count": 1, "max": 1, "min": 1, "name": "household"}]]
        ... }
        >>> has_axes(value)
        True

        >>> value = {
        ...     "persons": {"Javier": {"salary": {"2018-11": [2000, 3000]}}}
        ... }
        >>> has_axes(value)
        False

    """

    if not isinstance(value, dict):
        return False

    return value.get("axes", None) is not None
