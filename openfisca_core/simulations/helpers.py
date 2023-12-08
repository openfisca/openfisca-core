from __future__ import annotations

from typing import Type, Union

from openfisca_core.errors import SituationParsingError

from .typing import FullyDefinedParamsWithoutShortcut


def calculate_output_add(simulation, variable_name: str, period):
    return simulation.calculate_add(variable_name, period)


def calculate_output_divide(simulation, variable_name: str, period):
    return simulation.calculate_divide(variable_name, period)


def check_type(
    input: FullyDefinedParamsWithoutShortcut,
    input_type: Type[Union[dict, list, str]],
    path: list[str] | None = None,
) -> None:
    json_type_map = {
        dict: "Object",
        list: "Array",
        str: "String",
    }

    if path is None:
        path = []

    if not isinstance(input, input_type):
        raise SituationParsingError(
            path,
            "Invalid type: must be of type '{}'.".format(json_type_map[input_type]),
        )


def transform_to_strict_syntax(data):
    if isinstance(data, (str, int)):
        data = [data]
    if isinstance(data, list):
        return [str(item) if isinstance(item, int) else item for item in data]
    return data


def _get_person_count(input_dict):
    try:
        first_value = next(iter(input_dict.values()))
        if isinstance(first_value, dict):
            first_value = next(iter(first_value.values()))
        if isinstance(first_value, str):
            return 1

        return len(first_value)
    except Exception:
        return 1
