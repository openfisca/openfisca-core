from collections.abc import Iterable

from openfisca_core import errors

from .typing import ParamsWithoutAxes


def calculate_output_add(simulation, variable_name: str, period):
    return simulation.calculate_add(variable_name, period)


def calculate_output_divide(simulation, variable_name: str, period):
    return simulation.calculate_divide(variable_name, period)


def check_type(input, input_type, path=None) -> None:
    json_type_map = {
        dict: "Object",
        list: "Array",
        str: "String",
    }

    if path is None:
        path = []

    if not isinstance(input, input_type):
        raise errors.SituationParsingError(
            path,
            f"Invalid type: must be of type '{json_type_map[input_type]}'.",
        )


def check_unexpected_entities(
    params: ParamsWithoutAxes,
    entities: Iterable[str],
) -> None:
    """Check if the input contains entities that are not in the system.

    Args:
        params(ParamsWithoutAxes): Simulation parameters.
        entities(Iterable[str]): List of entities in plural form.

    Raises:
        SituationParsingError: If there are entities that are not in the system.

    Examples:
        >>> entities = {"persons", "households"}

        >>> params = {
        ...     "persons": {"Javier": {"salary": {"2018-11": 2000}}},
        ...     "households": {"household": {"parents": ["Javier"]}},
        ... }

        >>> check_unexpected_entities(params, entities)

        >>> params = {"dogs": {"Bart": {"damages": {"2018-11": 2000}}}}

        >>> check_unexpected_entities(params, entities)
        Traceback (most recent call last):
        openfisca_core.errors.situation_parsing_error.SituationParsingError

    """
    if has_unexpected_entities(params, entities):
        unexpected_entities = [entity for entity in params if entity not in entities]

        message = (
            "Some entities in the situation are not defined in the loaded tax "
            "and benefit system. "
            f"These entities are not found: {', '.join(unexpected_entities)}. "
            f"The defined entities are: {', '.join(entities)}."
        )

        raise errors.SituationParsingError([unexpected_entities[0]], message)


def has_unexpected_entities(params: ParamsWithoutAxes, entities: Iterable[str]) -> bool:
    """Check if the input contains entities that are not in the system.

    Args:
        params(ParamsWithoutAxes): Simulation parameters.
        entities(Iterable[str]): List of entities in plural form.

    Returns:
        bool: True if the input contains entities that are not in the system.

    Examples:
        >>> entities = {"persons", "households"}

        >>> params = {
        ...     "persons": {"Javier": {"salary": {"2018-11": 2000}}},
        ...     "households": {"household": {"parents": ["Javier"]}},
        ... }

        >>> has_unexpected_entities(params, entities)
        False

        >>> params = {"dogs": {"Bart": {"damages": {"2018-11": 2000}}}}

        >>> has_unexpected_entities(params, entities)
        True

    """
    return any(entity for entity in params if entity not in entities)


def transform_to_strict_syntax(data):
    if isinstance(data, (str, int)):
        data = [data]
    if isinstance(data, list):
        return [str(item) if isinstance(item, int) else item for item in data]
    return data
