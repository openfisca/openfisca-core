import os
import traceback

import numpy

from openfisca_core import parameters, periods
from openfisca_core.errors import ParameterParsingError
from openfisca_core.parameters import config


def contains_nan(vector):
    if numpy.issubdtype(vector.dtype, numpy.record):
        return any([contains_nan(vector[name]) for name in vector.dtype.names])
    else:
        return numpy.isnan(vector).any()


def load_parameter_file(file_path, name = ''):
    """
    Load parameters from a YAML file (or a directory containing YAML files).

    :returns: An instance of :class:`.ParameterNode` or :class:`.ParameterScale` or :class:`.Parameter`.
    """
    if not os.path.exists(file_path):
        raise ValueError("{} does not exist".format(file_path))
    if os.path.isdir(file_path):
        return parameters.ParameterNode(name, directory_path = file_path)
    data = _load_yaml_file(file_path)
    return _parse_child(name, data, file_path)


def _compose_name(path, child_name = None, item_name = None):
    if not path:
        return child_name
    if child_name is not None:
        return '{}.{}'.format(path, child_name)
    if item_name is not None:
        return '{}[{}]'.format(path, item_name)


def _load_yaml_file(file_path):
    with open(file_path, 'r') as f:
        try:
            return config.yaml.load(f, Loader = config.Loader)
        except (config.yaml.scanner.ScannerError, config.yaml.parser.ParserError):
            stack_trace = traceback.format_exc()
            raise ParameterParsingError(
                "Invalid YAML. Check the traceback above for more details.",
                file_path,
                stack_trace
                )
        except Exception:
            stack_trace = traceback.format_exc()
            raise ParameterParsingError(
                "Invalid parameter file content. Check the traceback above for more details.",
                file_path,
                stack_trace
                )


def _parse_child(child_name, child, child_path):
    if 'values' in child:
        return parameters.Parameter(child_name, child, child_path)
    elif 'brackets' in child:
        return parameters.ParameterScale(child_name, child, child_path)
    elif isinstance(child, dict) and all([periods.INSTANT_PATTERN.match(str(key)) for key in child.keys()]):
        return parameters.Parameter(child_name, child, child_path)
    else:
        return parameters.ParameterNode(child_name, data = child, file_path = child_path)


def _set_backward_compatibility_metadata(parameter, data):
    if data.get('unit') is not None:
        parameter.metadata['unit'] = data['unit']
    if data.get('reference') is not None:
        parameter.metadata['reference'] = data['reference']


def _validate_parameter(parameter, data, data_type = None, allowed_keys = None):
    type_map = {
        dict: 'object',
        list: 'array',
        }

    if data_type is not None and not isinstance(data, data_type):
        raise ParameterParsingError(
            "'{}' must be of type {}.".format(parameter.name, type_map[data_type]),
            parameter.file_path
            )

    if allowed_keys is not None:
        keys = data.keys()
        for key in keys:
            if key not in allowed_keys:
                raise ParameterParsingError(
                    "Unexpected property '{}' in '{}'. Allowed properties are {}."
                    .format(key, parameter.name, list(allowed_keys)),
                    parameter.file_path
                    )
