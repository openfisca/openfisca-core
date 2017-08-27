# -*- coding: utf-8 -*-


"""Handle legislative parameters."""


import os
import logging
import re

import yaml

from . import taxscales

log = logging.getLogger(__name__)

try:
    from yaml import CLoader as Loader
except ImportError:
    log.warning(
        "libyaml is not installed in your environement. This can make OpenFisca slower to start. Once you have installed libyaml, run 'pip uninstall pyyaml && pip install pyyaml' so that it is used in your Python environement.")
    from yaml import Loader


instant_pattern = re.compile("^\d{4}-\d{2}-\d{2}$")


def date_constructor(loader, node):
    return node.value


yaml.add_constructor(u'tag:yaml.org,2002:timestamp', date_constructor, Loader = Loader)


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


class ParameterParsingError(Exception):

    def __init__(self, message, file = None):
        if file is not None:
            message = (
                "Error parsing parameter file '{}':".format(file)
                + os.linesep
                + message
                ).encode('utf-8')
        super(ParameterParsingError, self).__init__(message)


class ValueAtInstant(object):
    allowed_value_types = [int, float, bool, type(None)]
    allowed_keys = set(['value', 'unit', 'reference'])

    def __init__(self, name, instant_str, yaml_object = None, value = None, file_path = None):
        """
            A value defined for a given instant.

            Can be instanciated from YAML data (use `yaml_object`), or given `value`.

            :param name: name of the parameter, eg "taxes.some_tax.some_param"
            :param instant_str: Date of the value in the format `YYYY-MM-DD`.
            :param yaml_object: Data loaded from a YAML file. If set, `value` should not be set.
            :param value: Used if and only if `yaml_object=None`. If `value=None`, the parameter is considered not defined at instant_str.
        """
        self.name = name
        self.instant_str = instant_str
        self.file_path = file_path

        if yaml_object is None:
            self.value = None
            return

        self.validate(yaml_object)

        if not isinstance(yaml_object, dict):
            raise ParameterParsingError(
                "'{}' must be of type object.".format(self.name).encode("utf-8"),
                file_path
                )
        try:
            value = yaml_object['value']
        except KeyError:
            raise ParameterParsingError(
                "Missing 'value' property for {}".format(name).encode('utf-8'),
                file_path
                )
        if type(value) not in self.allowed_value_types:
            raise ParameterParsingError(
                "Invalid value in {} : {}".format(name, value).encode('utf-8'),
                file_path
                )

        else:
            self.value = yaml_object['value']

    def validate(self, yaml_object):
        keys = yaml_object.keys()
        for key in keys:
            if key not in self.allowed_keys:
                raise ParameterParsingError(
                    "Unexpected property '{}' in '{}'. Allowed properties are {}."
                    .format(key, self.name, list(self.allowed_keys)).encode('utf-8'),
                    self.file_path
                    )

    def __eq__(self, other):
        return (self.name == other.name) and (self.instant_str == other.instant_str) and (self.value == other.value)


class ValuesHistory(object):
    def __init__(self, name, yaml_object, file_path = None):
        """
            A value defined for several periods.

            :param name: name of the parameter, eg "taxes.some_tax.some_param"
            :param yaml_object: Data loaded from a YAML file. In case of a reform, the data can also be created dynamically.
        """
        self.name = name

        if not isinstance(yaml_object, dict):
            raise ParameterParsingError(
                "'{}' must be of type object.".format(self.name).encode("utf-8"),
                file_path)

        instants = sorted(yaml_object.keys(), reverse = True)  # sort by antechronological order

        values_list = []
        for instant_str in instants:
            if not instant_pattern.match(instant_str):
                raise ParameterParsingError(
                    "Invalid property '{}' in '{}'. Properties must be valid YYYY-MM-DD instants, such as 2017-01-15."
                    .format(instant_str, self.name).encode('utf-8'),
                    file_path)

            instant_info = yaml_object[instant_str]

            #  Ignore expected values, as they are just metadata
            if instant_info == "expected" or isinstance(instant_info, dict) and instant_info.get("expected"):
                continue

            name = _compose_name(name, instant_str)
            value_at_instant = ValueAtInstant(name, instant_str, yaml_object = instant_info, file_path = file_path)
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
                    new_interval = ValueAtInstant(self.name, stop_str, yaml_object=None, value=overlapped_value)
                    new_values.append(new_interval)
                else:
                    new_interval = ValueAtInstant(self.name, stop_str, yaml_object=None, value=None)
                    new_values.append(new_interval)

        # Insert new interval
        new_interval = ValueAtInstant(self.name, start_str, yaml_object=None, value=value)
        new_values.append(new_interval)

        # Remove covered intervals
        while (i < n) and (old_values[i].instant_str >= start_str):
            i += 1

        # Past intervals : not affected
        while i < n:
            new_values.append(old_values[i])
            i += 1

        self.values_list = new_values


class Parameter(object):
    """
        Represents a parameter of the legislation.
    """
    allowed_keys = set(['values', 'description', 'unit', 'reference'])

    def __init__(self, name, yaml_object, file_path):
        self.name = name
        self.file_path = file_path
        self.validate(yaml_object)
        self.description = yaml_object.get('description')

        values = yaml_object['values']
        self.values_history = ValuesHistory(name, yaml_object = values, file_path = file_path)

    def validate(self, yaml_object):
        keys = yaml_object.keys()
        for key in keys:
            if key not in self.allowed_keys:
                raise ParameterParsingError(
                    "Unexpected property '{}' in parameter '{}'. Allowed properties are {}."
                    .format(key, self.name, list(self.allowed_keys)).encode('utf-8'),
                    self.file_path
                    )

    def _get_at_instant(self, instant_str):
        return self.values_history._get_at_instant(instant_str)


class Bracket(object):
    """
        A sclale bracket.
    """
    allowed_keys = set(['amount', 'threshold', 'rate', 'average_rate', 'base'])

    def __init__(self, name, yaml_object = None, file_path = None):
        """
        :param name: name of the bracket, eg "taxes.some_scale.bracket_3"
        :param yaml_object: Data loaded from a YAML file. In case of a reform, the data can also be created dynamically.
        """
        self.name = name
        self.validate(yaml_object)

        for key, value in yaml_object.items():
            new_child_name = _compose_name(name, key)
            new_child = ValuesHistory(new_child_name, value, file_path)
            setattr(self, key, new_child)

    def validate(self, yaml_object):
        keys = yaml_object.keys()
        for key in keys:
            if key not in self.allowed_keys:
                raise ParameterParsingError(
                    "Unexpected property '{}' in bracket '{}'. Allowed properties are {}."
                    .format(key, self.name, list(self.allowed_keys)).encode('utf-8')
                    )

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
    """
        A scale.
    """
    allowed_keys = set(['brackets', 'description', 'unit', 'reference'])

    def __init__(self, name, yaml_object, file_path):
        """
        :param name: name of the scale, eg "taxes.some_scale"
        :param yaml_object: Data loaded from a YAML file. In case of a reform, the data can also be created dynamically.
        """
        self.name = name
        self.file_path = file_path
        self.validate(yaml_object)
        self.description = yaml_object.get('description')

        brackets = []
        for i, bracket_data in enumerate(yaml_object['brackets']):
            bracket_name = _compose_name(name, i)
            bracket = Bracket(bracket_name, bracket_data, file_path)
            brackets.append(bracket)
        self.brackets = brackets

    def validate(self, yaml_object):
        keys = yaml_object.keys()
        for key in keys:
            if key not in self.allowed_keys:
                raise ParameterParsingError(
                    "Unexpected property '{}' in scale '{}'. Allowed properties are {}."
                    .format(key, self.name, list(self.allowed_keys)).encode('utf-8'),
                    self.file_path
                    )

        if not isinstance(yaml_object['brackets'], list):
            raise ParameterParsingError(
                "Property 'brackets' of scale '{}' must be a list."
                .format(self.name).encode('utf-8'),
                self.file_path
                )

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


def _parse_child(child_name, child, child_path):
    if 'values' in child:
        return Parameter(child_name, child, child_path)
    elif 'brackets' in child:
        return Scale(child_name, child, child_path)
    else:
        return Node(child_name, yaml_object = child, file_path = child_path)


class Node(object):
    """Node contains parameters of the legislation.

    Can be instanciated from YAML data already parsed and validated (use `yaml_object`), or given the path of a directory containing YAML files.
    """
    def __init__(self, name, directory_path = None, yaml_object = None, file_path = None):
        """
        :param name: Name of the node, eg "taxes.some_tax".
        :param directory_path: : Directory of YAML files describing the node. YAML files are parsed and transformed to python objects : `Node`, `Bracket`, `Scale`, `ValuesHistory` and `ValueAtInstant`.
        :param yaml_object` : Data extracted from a YAML file describing a Node.
        """
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
                    else:
                        child_name_expanded = _compose_name(name, child_name)
                        self.children[child_name] = _parse_child(child_name_expanded, data, child_path)

                elif os.path.isdir(child_path):
                    child_name = os.path.basename(child_path)
                    child_name_expanded = _compose_name(name, child_name)
                    self.children[child_name] = Node(child_name_expanded, directory_path = child_path)

        else:
            self.children = {}
            if not isinstance(yaml_object, dict):
                raise ParameterParsingError(
                    "'{}' must be of type object.".format(self.name).encode("utf-8"),
                    file_path
                    )
            for child_name, child in yaml_object.items():
                child_name_expanded = _compose_name(name, child_name)
                self.children[child_name] = _parse_child(child_name_expanded, child, file_path)

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
    return _parse_child(name, data, file_path)


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

    if not len(path_list) >= 1:
        raise ValueError('Trying to load parameters with no YAML directory given !')

    parameter_trees = []
    for path in path_list:
        parameter_tree = Node('', directory_path = path)
        parameter_trees.append(parameter_tree)

    base_parameter_tree = parameter_trees[0]  # is this really useful ?
    for i in range(1, len(parameter_trees)):
        parameter_tree = parameter_trees[i]
        base_parameter_tree._merge(parameter_tree)

    return base_parameter_tree
