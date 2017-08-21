# -*- coding: utf-8 -*-


"""Handle legislative parameters."""


import os
import logging
import re

import yaml
import jsonschema

from . import taxscales

log = logging.getLogger(__name__)

try:
    from yaml import CLoader as Loader
except ImportError:
    log.warning("...") # TODO: add a warning message to suggest installing libyaml
    from yaml import Loader

node_keywords = ['reference', 'description']

schema_index = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "Node metadata YAML file",
    "description": "A file named _.yaml that contains metadata about a parameter node.",
    "type": "object",
    "properties": {
        "description": {
            "type": "string",
            },
        "reference": {
            "type": "string",
            },
        },
    "additionalProperties": False,
    }

schema_yaml = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "YAML parameter file",
    "description": "A YAML file that can contain a node, a parameter or a scale.",
    "definitions": {
        "value": {
            "anyOf": [
                {
                    "type": "number",
                    },
                {
                    "type": "boolean",
                    },
                {
                    "type": "null",
                    },
                ],
            },
        "values_history": {
            "type": "object",
            "patternProperties": {
                "^\d{4}-\d{2}-\d{2}$": {
                    "anyOf": [
                        {
                            "type": "string",
                            "enum": ["expected"],
                            },
                        {
                            "type": "object",
                            "properties": {
                                "expected": {"$ref": "#/definitions/value"},
                                "reference": {
                                    "type": "string",
                                    },
                                },
                            "required": ["expected"],
                            "additionalProperties": False,
                            },
                        {
                            "type": "object",
                            "properties": {
                                "value": {"$ref": "#/definitions/value"},
                                "reference": {
                                    "type": "string",
                                    },
                                },
                            "required": ["value"],
                            "additionalProperties": False,
                            },
                        ],
                    },
                },
            "additionalProperties": False,
            },
        "node": {
            "type": "object",
            "patternProperties": {
                "^(?!(brackets|values|description|reference)$)": {"$ref": "#/definitions/node_or_parameter_of_scale"},
                "^description$": {
                    "type": "string",
                    },
                "^reference$": {
                    "type": "string",
                    },
                },
            "additionalProperties": False,
            },

        "parameter": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    },
                "reference": {
                    "type": "string",
                    },
                "unit": {
                    "type": "string",
                    "enum": ['/1', 'currency', 'year'],
                    },
                "values": {"$ref": "#/definitions/values_history"},
                },
            "required": ["values"],
            "additionalProperties": False,
            },
        "scale": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    },
                "reference": {
                    "type": "string",
                    },
                "unit": {
                    "type": "string",
                    "enum": ['/1', 'currency', 'year'],
                    },
                "brackets": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "amount": {"$ref": "#/definitions/values_history"},
                            "threshold": {"$ref": "#/definitions/values_history"},
                            "rate": {"$ref": "#/definitions/values_history"},
                            "average_rate": {"$ref": "#/definitions/values_history"},
                            "base": {"$ref": "#/definitions/values_history"},
                            },
                        "additionalProperties": False,
                        },
                    },
                },
            "required": ["brackets"],
            "additionalProperties": False,
            },
        "node_or_parameter_of_scale": {
            "anyOf": [
                {"$ref": "#/definitions/node"},
                {"$ref": "#/definitions/parameter"},
                {"$ref": "#/definitions/scale"},
                ],
            },
        },
    "$ref": "#/definitions/node_or_parameter_of_scale",
    }

instant_pattern = re.compile("^\d{4}-\d{2}-\d{2}$")

def date_constructor(loader, node):
    return node.value



yaml.add_constructor(u'tag:yaml.org,2002:timestamp', date_constructor, Loader = Loader)


validator_index = jsonschema.Draft4Validator(schema_index)
validator_yaml = jsonschema.Draft4Validator(schema_yaml)


class ParameterNotFound(Exception):
    """Exception raised when a parameter is not found in the parameters.
    """
    def __init__(self, name, instant_str, variable_name = None):
        """
        :param name: Name of the parameter
        :instant_str: Instant where the parameter does not exist, in the format `YYYY-MM-DD`.
        :variable_name: If the parameter was queried during the computation of a variable, name of that variable.
        """
        assert name is not None
        assert instant_str is not None
        self.name = name
        self.instant_str = instant_str
        self.variable_name = variable_name
        message = u"The parameter '{}'".format(name)
        if variable_name is not None:
            message += u" requested by variable '{}'".format(variable_name)
        message += (
            u" was not found in the {2} tax and benefit system."
            ).format(name, variable_name, instant)
        super(ParameterNotFound, self).__init__(message)


class ExceptionValueIsUnknown(Exception):
    pass


class ValueAtInstant(object):
    allowed_value_types = [int, float, bool, type(None)]
    def __init__(self, name, instant_str, validated_yaml=None, value=None):
        """A value defined for a given instant.

        Can be instanciated from YAML data (use `validated_yaml`), or given `value`.

        :param name: name of the parameter, eg "taxes.some_tax.some_param"
        :param instant_str: Date of the value in the format `YYYY-MM-DD`.
        :param validated_yaml: Data loaded from a YAML file and validated. If set, `value` should not be set.
        :param value: Used if and only if `validated_yaml=None`. If `value=None`, the parameter is considered not defined at instant_str.
        """
        self.name = name
        self.instant_str = instant_str

        if not validated_yaml == 'expected':
            for key in ['expected', 'value']:
                value = validated_yaml.get(key)
                if type(value) not in self.allowed_value_types:
                    raise ValueError("Invalid value in {}: {}".format(name, value).encode('utf-8'))

        if validated_yaml is not None:
            if validated_yaml == 'expected' or validated_yaml == {'expected': None}:
                raise ExceptionValueIsUnknown()
            elif 'expected' in validated_yaml:
                self.value = validated_yaml['expected']
            elif validated_yaml['value'] is None:
                self.value = None
            else:
                self.value = validated_yaml['value']

        else:
            self.value = value

    def __eq__(self, other):
        return (self.name == other.name) and (self.instant_str == other.instant_str) and (self.value == other.value)


class ValuesHistory(object):
    def __init__(self, name, validated_yaml):
        """A value defined for several periods.

        :param name: name of the parameter, eg "taxes.some_tax.some_param"
        :param validated_yaml: Data loaded from a YAML file and validated. In case of a reform, the data can also be created dynamically.
        """
        self.name = name

        instants = sorted(validated_yaml.keys(), reverse=True)    # sort by antechronological order
        assert len(set(instants)) == len(instants), "Instants in values history should be unique"

        values_list = []
        for instant_str in instants:
            instant_info = validated_yaml[instant_str]
            try:
                value_at_instant = ValueAtInstant(_compose_name(name, instant_str), instant_str, validated_yaml=instant_info)
            except ExceptionValueIsUnknown:
                pass
            else:
                values_list.append(value_at_instant)

        self.values_list = values_list

    def __repr__(self):
        return 'ValuesHistory "{}"\n'.format(self.name) + ''.join('  {}: {}\n'.format(value.instant_str, value.value) for value in self.values_list)

    def __eq__(self, other):
        return (self.name == other.name) and (self.values_list == other.values_list)

    def _get_at_instant(self, instant_str):
        for value_at_instant in self.values_list:
            if value_at_instant.instant_str <= instant_str:
                return value_at_instant.value
        return None

    def update(self, period=None, start=None, stop=None, value=None):
        """Change the value for a given period.

        :param period: Period where the value is modified. If set, `start` and `stop` should be `None`.
        :param start: Start of the period. Instance of `openfisca_core.periods.Instant`. If set, `period` should be `None`.
        :param stop: Stop of the period. Instance of `openfisca_core.periods.Instant`. If set, `period` should be `None`.
        :param value: New value. If `None`, the parameter is removed from the legislation parameters for the given period.
        """
        if period is not None:
            assert start is None and stop is None, u'period parameter can\'t be used with start and stop'
            start = period.start
            stop = period.stop
        assert start is not None, u'start must be provided, or period'
        start_str = str(start)
        stop_str = str(stop.offset(1, 'day')) if stop else None

        old_values = self.values_list
        new_values = []
        n = len(old_values)
        i = 0

        # Future intervals : not affected
        if stop_str:
            while (i < n) and (old_values[i].instant_str >= stop_str):
                new_values.append(old_values[i])
                i += 1

        # Right-overlapped interval
        if stop_str:
            if new_values and (stop_str == new_values[-1].instant_str):
                pass  # such interval is empty
            else:
                if i < n:
                    overlapped_value = old_values[i].value
                    new_interval = ValueAtInstant(self.name, stop_str, validated_yaml=None, value=overlapped_value)
                    new_values.append(new_interval)
                else:
                    new_interval = ValueAtInstant(self.name, stop_str, validated_yaml=None, value=None)
                    new_values.append(new_interval)

        # Insert new interval
        new_interval = ValueAtInstant(self.name, start_str, validated_yaml=None, value=value)
        new_values.append(new_interval)

        # Remove covered intervals
        while (i < n) and (old_values[i].instant_str >= start_str):
            i += 1

        # Past intervals : not affected
        while i < n:
            new_values.append(old_values[i])
            i += 1

        self.values_list = new_values


class Parameter(ValuesHistory):
    """A wrapper over a `ValuesHistory` object.

    Use this class to represent a parameter of the legislation. Use directly a `ValuesHistory` to represent values of a member of a scale bracket.
    """
    def __init__(self, name, validated_yaml):
        if 'description' in validated_yaml:
            self.description = validated_yaml['description']

        values = validated_yaml['values']
        super(Parameter, self).__init__(name, validated_yaml=values)


class Bracket(object):
    """A bracket of a scale.
    """
    def __init__(self, name, validated_yaml=None):
        """
        :param name: name of the bracket, eg "taxes.some_scale.bracket_3"
        :param validated_yaml: Data loaded from a YAML file and validated. In case of a reform, the data can also be created dynamically.
        """
        self.name = name

        for key, value in validated_yaml.items():
            if key in {'amount', 'rate', 'average_rate', 'threshold', 'base'}:
                new_child_name = _compose_name(name, key)
                new_child = ValuesHistory(new_child_name, value)
                setattr(self, key, new_child)
            else:
                raise ValueError("Invalid bracket attribute in {}: {}".format(name, key).encode('utf-8'))


    def _get_at_instant(self, instant_str):
        return BracketAtInstant(self.name, self, instant_str)


class BracketAtInstant(object):
    """A bracket of a scale at a given instant.

    This class is used temporarily in `Scale._get_at_instant()`, before the construction of a tax scale.
    """
    def __init__(self, name, bracket, instant_str):
        """
        :param name: Name of the bracket, eg "taxes.some_scale.bracket_3"
        :param bracket: Original `Bracket` object.
        :param instant_str: Date in the format `YYYY-MM-DD`.
        """
        self.name = name
        self.instant_str = instant_str

        for key in ['amount', 'rate', 'average_rate', 'threshold', 'base']:
            if hasattr(bracket, key):
                new_child = getattr(bracket, key)._get_at_instant(instant_str)
                if new_child is not None:
                    setattr(self, key, new_child)


class Scale(object):
    """A scale.
    """
    def __init__(self, name, validated_yaml):
        """
        :param name: name of the scale, eg "taxes.some_scale"
        :param validated_yaml: Data loaded from a YAML file and validated. In case of a reform, the data can also be created dynamically.
        """
        self.name = name
        if 'description' in validated_yaml:
            self.description = validated_yaml['description']

        brackets = []
        for i, bracket_data in enumerate(validated_yaml['brackets']):
            bracket_name = _compose_name(name, i)
            bracket = Bracket(bracket_name, bracket_data)
            brackets.append(bracket)
        self.brackets = brackets

    def _get_at_instant(self, instant_str):
        brackets = [bracket._get_at_instant(instant_str) for bracket in self.brackets]

        if any(hasattr(bracket, 'amount') for bracket in brackets):
            scale = taxscales.AmountTaxScale()
            for bracket in brackets:
                if hasattr(bracket, 'amount') and hasattr(bracket, 'threshold'):
                    amount = bracket.amount
                    threshold = bracket.threshold
                    scale.add_bracket(threshold, amount)
        elif any(hasattr(bracket, 'average_rate') for bracket in brackets):
            scale = taxscales.LinearAverageRateTaxScale()

            for bracket in brackets:
                if hasattr(bracket, 'base'):
                    base = bracket.base
                else:
                    base = 1.
                if hasattr(bracket, 'average_rate') and hasattr(bracket, 'threshold'):
                    average_rate = bracket.average_rate
                    threshold = bracket.threshold
                    scale.add_bracket(threshold, average_rate * base)
            return scale
        else:
            scale = taxscales.MarginalRateTaxScale()

            for bracket in brackets:
                if hasattr(bracket, 'base'):
                    base = bracket.base
                else:
                    base = 1.
                if hasattr(bracket, 'rate') and hasattr(bracket, 'threshold'):
                    rate = bracket.rate
                    threshold = bracket.threshold
                    scale.add_bracket(threshold, rate * base)
            return scale

    def __getitem__(self, key):
        if isinstance(key, int) and key < len(self.brackets):
            return self.brackets[key]
        else:
            raise KeyError(key)


def _parse_child(child_name, child):
    if 'values' in child:
        return Parameter(child_name, child)
    elif 'brackets' in child:
        return Scale(child_name, child)
    else:
        return Node(child_name, validated_yaml=child)


# def _validate_against_schema(file_path, parsed_yaml, validator):
#     try:
#         validator.validate(parsed_yaml)
#     except jsonschema.exceptions.ValidationError:
#         raise ValueError('Invalid parameter file {}'.format(file_path))


class Node(object):
    """Node contains parameters of the legislation.

    Can be instanciated from YAML data already parsed and validated (use `validated_yaml`), or given the path of a directory containing YAML files.
    """
    def __init__(self, name, directory_path=None, validated_yaml=None, children=None):
        """
        :param name: Name of the node, eg "taxes.some_tax".
        :param directory_path: : Directory of YAML files describing the node. YAML files are parsed, validated and transformed to python objects : `Node`, `Bracket`, `Scale`, `ValuesHistory` and `ValueAtInstant`.
        :param validated_yaml` : Data extracted from a YAML file describing a Node.
        """
        assert isinstance(name, str)
        self.name = name

        if directory_path:
            self.children = {}
            for child_name in os.listdir(directory_path):
                child_path = os.path.join(directory_path, child_name)
                if os.path.isfile(child_path):
                    child_name, ext = os.path.splitext(child_name)
                    assert ext == '.yaml', "The parameter directory should contain only YAML files."
                    with open(child_path, 'r') as f:
                        data = yaml.load(f, Loader = Loader)

                    if child_name == 'index':
                        pass
                        # _validate_against_schema(child_path, data, validator_index)
                    else:
                        # _validate_against_schema(child_path, data, validator_yaml)
                        child_name_expanded = _compose_name(name, child_name)
                        self.children[child_name] = _parse_child(child_name_expanded, data)

                elif os.path.isdir(child_path):
                    child_name = os.path.basename(child_path)
                    child_name_expanded = _compose_name(name, child_name)
                    self.children[child_name] = Node(child_name_expanded, directory_path=child_path)
                else:
                    raise ValueError('Unexpected item {}'.format(child_path))

        else:
            self.children = {}
            for child_name, child in validated_yaml.items():
                if child_name in node_keywords:
                    continue
                child_name_expanded = _compose_name(name, child_name)
                self.children[child_name] = _parse_child(child_name_expanded, child)

    def _get_at_instant(self, instant_str):
        return NodeAtInstant(self.name, self, instant_str)

    def _merge(self, other):
        for child_name, child in other.children.items():
            self.children[child_name] = child

    def add_child(self, name, child):
        """
        Add a new child to the node.

        :param name: Name of the child that must be used to access that child. Should not contain anything that could interfere with the operator `.` (dot).
        :param child: The new child, an instance of `Scale` or `Parameter` or `Node`.
        """
        assert name not in self.children
        assert isinstance(child, Node) or isinstance(child, Parameter) or isinstance(child, Scale)
        self.children[name] = child

    def __getattr__(self, key):
        if not hasattr(self, 'children'):   # during deserialization, self.children does not yet exist
            raise AttributeError(key)

        if key in self.children:
            return self.children[key]
        else:
            raise AttributeError(key)


def load_file(name, file_path):
    """
    Load parameters from a YAML file.

    :returns: An instance of `Node` or `Scale` or `Parameter`.
    """
    with open(file_path, 'r') as f:
        data = yaml.load(f)
    # _validate_against_schema(file_path, data, validator_yaml)
    return _parse_child(name, data)


class NodeAtInstant(object):
    """Parameters of the legislation, at a given instant.
    """
    def __init__(self, name, node, instant_str):
        """
        :param name: Name of the node.
        :param node: Original `Node` instance.
        :param instant_str: A date in the format `YYYY-MM-DD`.
        """
        self.name = name
        self.instant_str = instant_str
        self.children = {}
        for child_name, child in node.children.items():
            child_at_instant = child._get_at_instant(instant_str)
            if child_at_instant is not None:
                self.children[child_name] = child_at_instant

    def __getattr__(self, key):
        if key not in self.children:
            param_name = _compose_name(self.name, key)
            raise ParameterNotFound(param_name, self.instant_str)
        return self.children[key]

    def __getitem__(self, key):  # deprecated
        return getattr(self, key)

    def __iter__(self):
        return iter(self.children)


def _compose_name(path, child_name):
    if path:
        if isinstance(child_name, int)or instant_pattern.match(child_name):
            return '{}[{}]'.format(path, child_name)
        return '{}.{}'.format(path, child_name)
    else:
        return child_name


def load_parameters(path_list):
    '''Load the parameters of a legislation from a directory containing YAML files.

    If several directories are parsed, newer children with the same name are not merged but overwrite previous ones.

    :param path_list: List of absolute paths.
    '''

    assert len(path_list) >= 1, 'Trying to load parameters with no YAML directory given !'


    parameter_trees = []
    for path in path_list:
        parameter_tree = Node('', directory_path=path)
        parameter_trees.append(parameter_tree)

    base_parameter_tree = parameter_trees[0]
    for i in range(1, len(parameter_trees)):
        parameter_tree = parameter_trees[i]
        base_parameter_tree._merge(parameter_tree)

    return base_parameter_tree
