import os
import traceback

import numpy

from openfisca_core import parameters, periods
from openfisca_core.errors import ParameterParsingError
from openfisca_core.parameters import config


def contains_nan(vector):
    if numpy.issubdtype(vector.dtype, numpy.record) or numpy.issubdtype(
        vector.dtype,
        numpy.void,
    ):
        return any(contains_nan(vector[name]) for name in vector.dtype.names)
    return numpy.isnan(vector).any()


def load_parameter_file(file_path, name=""):
    """Load parameters from a YAML file (or a directory containing YAML files).

    :returns: An instance of :class:`.ParameterNode` or :class:`.ParameterScale` or :class:`.Parameter`.
    """
    if not os.path.exists(file_path):
        msg = f"{file_path} does not exist"
        raise ValueError(msg)
    if os.path.isdir(file_path):
        return parameters.ParameterNode(name, directory_path=file_path)
    data = _load_yaml_file(file_path)
    return _parse_child(name, data, file_path)


def _compose_name(path, child_name=None, item_name=None):
    if not path:
        return child_name
    if child_name is not None:
        return f"{path}.{child_name}"
    if item_name is not None:
        return f"{path}[{item_name}]"
    return None


def _load_yaml_file(file_path):
    with open(file_path) as f:
        try:
            return config.yaml.load(f, Loader=config.Loader)
        except (config.yaml.scanner.ScannerError, config.yaml.parser.ParserError):
            stack_trace = traceback.format_exc()
            msg = "Invalid YAML. Check the traceback above for more details."
            raise ParameterParsingError(
                msg,
                file_path,
                stack_trace,
            )
        except Exception:
            stack_trace = traceback.format_exc()
            msg = "Invalid parameter file content. Check the traceback above for more details."
            raise ParameterParsingError(
                msg,
                file_path,
                stack_trace,
            )


def _parse_child(child_name, child, child_path):
    if "values" in child:
        return parameters.Parameter(child_name, child, child_path)
    if "brackets" in child:
        return parameters.ParameterScale(child_name, child, child_path)
    if isinstance(child, dict) and all(
        periods.INSTANT_PATTERN.match(str(key)) for key in child
    ):
        return parameters.Parameter(child_name, child, child_path)
    return parameters.ParameterNode(child_name, data=child, file_path=child_path)


def _set_backward_compatibility_metadata(parameter, data) -> None:
    if data.get("unit") is not None:
        parameter.metadata["unit"] = data["unit"]
    if data.get("reference") is not None:
        parameter.metadata["reference"] = data["reference"]


def _validate_parameter(parameter, data, data_type=None, allowed_keys=None) -> None:
    type_map = {
        dict: "object",
        list: "array",
    }

    if data_type is not None and not isinstance(data, data_type):
        msg = f"'{parameter.name}' must be of type {type_map[data_type]}."
        raise ParameterParsingError(
            msg,
            parameter.file_path,
        )

    if allowed_keys is not None:
        keys = data.keys()
        for key in keys:
            if key not in allowed_keys:
                msg = f"Unexpected property '{key}' in '{parameter.name}'. Allowed properties are {list(allowed_keys)}."
                raise ParameterParsingError(
                    msg,
                    parameter.file_path,
                )
