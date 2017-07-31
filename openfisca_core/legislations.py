# -*- coding: utf-8 -*-


"""Handle legislative parameters in JSON format."""


import os

import yaml
from jsonschema import validate

from . import taxscales


node_keywords = ['type', 'reference', 'description']

schema_node_meta = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "Node metadata YAML file",
    "description": "A file named _.yaml that contains metadata about a parameter node.",
    "type": "object",
    "properties": {
        "type": {
            "enum": ["node"],
            },
        "description": {
            "type": "string",
            },
        "reference": {
            "type": "string",
            },
        },
    "required": ["type"],
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
            "properties": {
                "type": {
                    "enum": ["node"],
                    },
                "description": {
                    "type": "string",
                    },
                "reference": {
                    "type": "string",
                    },
                },
            "required": ["type"],
            "additionalProperties": {"$ref": "#/definitions/node_or_parameter_of_scale"},
            },
        "parameter": {
            "type": "object",
            "properties": {
                "type": {
                    "enum": ["parameter"],
                    },
                "description": {
                    "type": "string",
                    },
                "reference": {
                    "type": "string",
                    },
                "unit": {
                    "type": "string",
                    "enum": ['/1', 'currency'],
                    },
                "values": {"$ref": "#/definitions/values_history"},
                },
            "required": ["type", "values"],
            "additionalProperties": False,
            },
        "scale": {
            "type": "object",
            "properties": {
                "type": {
                    "enum": ["scale"],
                    },
                "description": {
                    "type": "string",
                    },
                "reference": {
                    "type": "string",
                    },
                "brackets": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "amount": {"$ref": "#/definitions/values_history"},
                            "threshold": {"$ref": "#/definitions/values_history"},
                            "rate": {"$ref": "#/definitions/values_history"},
                            "base": {"$ref": "#/definitions/values_history"},
                            },
                        "additionalProperties": False,
                        },
                    },
                },
            "required": ["type", "brackets"],
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


class ParameterNotFound(Exception):
    def __init__(self, name, instant_str, variable_name = None):
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
    def __init__(self, name, instant_str, yaml_data=None, value=None):
        """
            Can be instanciated from YAML data (use yaml_data), or dynamically for reforms.

            name : name of the parameter, eg "a.b.param"
            instant_str : Date of the value.
            yaml_data : Data extracted from the yaml. If set, value should not be set.
            value : Used if and only if yaml_data=None. If value=None, the parameter is removed from the legislation.
        """
        self.name = name
        self.instant_str = instant_str

        if yaml_data is not None:
            if yaml_data == 'expected' or yaml_data == {'expected': None}:
                raise ExceptionValueIsUnknown()
            elif 'expected' in yaml_data:
                self.value = yaml_data['expected']
            elif yaml_data['value'] is None:
                self.value = None
            else:
                self.value = yaml_data['value']

        else:
            self.value = value

    def __eq__(self, other):
        return (self.name == other.name) and (self.instant_str == other.instant_str) and (self.value == other.value)


class ValuesHistory(object):
    def __init__(self, name, yaml_data=None, values_list=None):
        """
            name : name of the parameter, eg "a.b.param"
            yaml_data : Data extracted from the yaml. If set, values_list should not be set.
            values_list : List of ValueAtInstant objects. If set, yaml_data should not be set.
        """
        self.name = name

        if yaml_data:
            instants = sorted(yaml_data.keys(), reverse=True)    # sort by antechronological order
            assert len(set(instants)) == len(instants), "Instants in values history should be unique"
            values_list = []
            for instant_str in instants:
                instant_info = yaml_data[instant_str]
                if instant_info is None:
                    print(yaml_data)
                try:
                    value_at_instant = ValueAtInstant(name, instant_str, yaml_data=instant_info)
                except ExceptionValueIsUnknown:
                    pass
                else:
                    values_list.append(value_at_instant)
        else:
            values_list = sorted(values_list, key=lambda x: x.instant_str, reverse=True)

        self.values_list = values_list

    def __repr__(self):
        return 'ValuesHistory "{}"\n'.format(self.name) + ''.join('  {}: {}\n'.format(value.instant_str, value.value) for value in self.values_list)

    def __eq__(self, other):
        return (self.name == other.name) and (self.values_list == other.values_list)

    def get_at_instant(self, instant_str):
        for value_at_instant in self.values_list:
            if value_at_instant.instant_str <= instant_str:
                return value_at_instant.value
        return None

    def update(self, period=None, start=None, stop=None, value=None):
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
                    new_interval = ValueAtInstant(self.name, stop_str, yaml_data=None, value=overlapped_value)
                    new_values.append(new_interval)
                else:
                    new_interval = ValueAtInstant(self.name, stop_str, yaml_data=None, value=None)
                    new_values.append(new_interval)

        # Insert new interval
        new_interval = ValueAtInstant(self.name, start_str, yaml_data=None, value=value)
        new_values.append(new_interval)

        # Remove covered intervals
        while (i < n) and (old_values[i].instant_str >= start_str):
            i += 1

        # Past intervals : not affected
        while i < n:
            new_values.append(old_values[i])
            i += 1

        self.values_list = new_values


class Bracket(object):
    def __init__(self, name, yaml_data):
        self.name = name

        for key, value in yaml_data.items():
            if key in {'amount', 'rate', 'threshold', 'base'}:
                new_child_name = compose_name(name, key)
                new_child = ValuesHistory(new_child_name, value)
                setattr(self, key, new_child)

    def get_at_instant(self, instant_str):
        return BracketAtInstant(self.name, self, instant_str)


class BracketAtInstant(object):
    '''This class is used temporarily in Scale._get_at_instant, before the construction of a tax scale'''
    def __init__(self, name, bracket, instant_str):
        self.name = name
        self.instant_str = instant_str

        for key in ['amount', 'rate', 'threshold', 'base']:
            if hasattr(bracket, key):
                new_child = getattr(bracket, key).get_at_instant(instant_str)
                if new_child is not None:
                    setattr(self, key, new_child)


class Scale(object):
    def __init__(self, name, yaml_data):
        self.name = name

        brackets = []
        for i, bracket_data in enumerate(yaml_data['brackets']):
            bracket_name = str(i)
            bracket = Bracket(bracket_name, bracket_data)
            brackets.append(bracket)
        self.brackets = brackets

    def get_at_instant(self, instant_str):
        brackets = [bracket.get_at_instant(instant_str) for bracket in self.brackets]

        if any(hasattr(bracket, 'amount') for bracket in brackets):
            scale = taxscales.AmountTaxScale()
            for bracket in brackets:
                if hasattr(bracket, 'amount') and hasattr(bracket, 'threshold'):
                    amount = bracket.amount
                    threshold = bracket.threshold
                    scale.add_bracket(threshold, amount)
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


class Node(object):
    def __init__(self, name, path=None, yaml_data=None, children=None):
        """
            name : name of the node, eg "a.b"
            path : directory of YAML files describing the node
            yaml_data : Data extracted from a yaml file describing a Node
            children : Dictionary of ValuesHistory or Scale objects indexed by name.

            Only one of the 3 parameters path, yaml_data or children should be set.
        """
        assert isinstance(name, str)
        self.name = name

        def parse_child(child_name, child):
            if child['type'] == 'parameter':
                return ValuesHistory(child_name, child['values'])
            elif child['type'] == 'scale':
                return Scale(child_name, child)
            elif child['type'] == 'node':
                return Node(child_name, yaml_data=child)

        if path:
            self.children = {}
            for child_name in os.listdir(path):
                child_path = os.path.join(path, child_name)
                if os.path.isfile(child_path):
                    child_name, ext = os.path.splitext(child_name)
                    assert ext == '.yaml', "The parameter directory should contain only YAML files."
                    with open(child_path, 'r') as f:
                        data = yaml.load(f)

                    if child_name == '_':
                        validate(data, schema_node_meta)
                    else:
                        validate(data, schema_yaml)
                        child_name_expanded = compose_name(name, child_name)
                        self.children[child_name] = parse_child(child_name_expanded, data)

                elif os.path.isdir(child_path):
                    child_name = os.path.basename(child_path)
                    child_name_expanded = compose_name(name, child_name)
                    self.children[child_name] = Node(child_name_expanded, path=child_path)
                else:
                    raise ValueError('Unexpected item {}'.format(child_path))

        elif yaml_data:
            self.children = {}
            for child_name, child in yaml_data.items():
                if child_name in node_keywords:
                    continue
                child_name_expanded = compose_name(name, child_name)
                self.children[child_name] = parse_child(child_name_expanded, child)

        else:
            for child in children.values():
                assert isinstance(child, Node) or isinstance(child, Scale) or isinstance(child, ValuesHistory), child
            self.children = children

    def get_at_instant(self, instant_str):
        return NodeAtInstant(self.name, self, instant_str)

    def merge(self, other):
        for child_name, child in other.children.items():
            self.children[child_name] = child


class NodeAtInstant(object):
    def __init__(self, name, node, instant_str):
        self.name = name
        self.instant_str = instant_str
        self.children = {}
        for child_name, child in node.children.items():
            child_at_instant = child.get_at_instant(instant_str)
            if child_at_instant is not None:
                self.children[child_name] = child_at_instant

    def __getattr__(self, key):
        if key not in {'children'}:
            if key not in self.children:
                param_name = compose_name(self.name, key)
                raise ParameterNotFound(param_name, self.instant_str)
            return self.children[key]

    def __getitem__(self, key):
        return getattr(self, key)

    def __iter__(self):
        return iter(self.children)


def compose_name(path, child_name):
    if path:
        return '{}.{}'.format(path, child_name)
    else:
        return child_name


def load_legislation(path_list):
    '''load_legislation() : load YAML directories

    If several directories are parsed, newer children with the same name are not merged but overwrite previous ones.
    '''

    assert len(path_list) >= 1, 'Trying to load parameters with no YAML directory given !'

    legislations = []
    for path in path_list:
        legislation = Node('', path=path)
        legislations.append(legislation)

    base_legislation = legislations[0]
    for i in range(1, len(legislations)):
        legislation = legislations[i]
        base_legislation.merge(legislation)

    return base_legislation
