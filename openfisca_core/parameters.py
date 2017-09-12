# -*- coding: utf-8 -*-


"""Handle legislative parameters."""


import os
import logging
import re
import traceback

import yaml

from . import taxscales

log = logging.getLogger(__name__)

try:
    from yaml import CLoader as Loader
except ImportError:
    log.warning(
        "libyaml is not installed in your environement. This can make OpenFisca slower to start. Once you have installed libyaml, run 'pip uninstall pyyaml && pip install pyyaml' so that it is used in your Python environement.")
    from yaml import Loader


PARAM_FILE_EXTENSIONS = {'.yaml', '.yml'}
INSTANT_PATTERN = re.compile("^\d{4}-\d{2}-\d{2}$")


def date_constructor(loader, node):
    return node.value


yaml.add_constructor(u'tag:yaml.org,2002:timestamp', date_constructor, Loader = Loader)


class ParameterNotFound(Exception):
    """
        Exception raised when a parameter is not found in the parameters.
    """
    def __init__(self, name, instant_str, variable_name = None):
        """
        :param name: Name of the parameter
        :param instant_str: Instant where the parameter does not exist, in the format `YYYY-MM-DD`.
        :param variable_name: If the parameter was queried during the computation of a variable, name of that variable.
        """
        self.name = name
        self.instant_str = instant_str
        self.variable_name = variable_name
        message = u"The parameter '{}'".format(name)
        if variable_name is not None:
            message += u" requested by variable '{}'".format(variable_name)
        message += (
            u" was not found in the {2} tax and benefit system."
            ).format(name, variable_name, instant_str)
        super(ParameterNotFound, self).__init__(message)


class ParameterParsingError(Exception):
    """
        Exception raised when a parameter cannot be parsed.
    """

    def __init__(self, message, file = None, traceback = None):
        """
        :param message: Error message
        :param file: Parameter file which caused the error (optional)
        :param traceback: Traceback (optional)
        """
        if file is not None:
            message = (
                "Error parsing parameter file '{}':".format(file)
                + os.linesep
                + message
                ).encode('utf-8')
        if traceback is not None:
            message = os.linesep + traceback + os.linesep + message
        super(ParameterParsingError, self).__init__(message)


class AbstractParameter(object):
    allowed_keys = None
    _data_type = None
    type_map = {
        dict: 'object',
        list: 'array',
        }

    def validate(self, data):
        if self._data_type is not None and not isinstance(data, self._data_type):
            raise ParameterParsingError(
                "'{}' must be of type {}.".format(self.name, self.type_map[self._data_type]).encode("utf-8"),
                self.file_path
                )

        if self.allowed_keys is not None:
            keys = data.keys()
            for key in keys:
                if key not in self.allowed_keys:
                    raise ParameterParsingError(
                        "Unexpected property '{}' in '{}'. Allowed properties are {}."
                        .format(key, self.name, list(self.allowed_keys)).encode('utf-8'),
                        self.file_path
                        )


class ValueAtInstant(AbstractParameter):
    """
        A value of a parameter at a given instant.
    """

    allowed_value_data_types = [int, float, bool, type(None)]
    allowed_keys = set(['value', 'unit', 'reference'])
    _data_type = dict

    def __init__(self, name, instant_str, data = None, file_path = None):
        """
            :param name: name of the parameter, e.g. "taxes.some_tax.some_param"
            :param instant_str: Date of the value in the format `YYYY-MM-DD`.
            :param data: Data, usually loaded from a YAML file.
        """
        self.name = name
        self.instant_str = instant_str
        self.file_path = file_path

        if data is None:
            self.value = None
            return

        self.validate(data)
        self.value = data['value']

    def validate(self, data):
        super(ValueAtInstant, self).validate(data)
        try:
            value = data['value']
        except KeyError:
            raise ParameterParsingError(
                "Missing 'value' property for {}".format(self.name).encode('utf-8'),
                self.file_path
                )
        if type(value) not in self.allowed_value_data_types:
            raise ParameterParsingError(
                "Invalid value in {} : {}".format(self.name, value).encode('utf-8'),
                self.file_path
                )

    def __eq__(self, other):
        return (self.name == other.name) and (self.instant_str == other.instant_str) and (self.value == other.value)

    def __repr__(self):
        return "ValueAtInstant({})".format({self.instant_str: self.value}).encode('utf-8')


class ValuesHistory(AbstractParameter):
    """
        This history of a parameter values.

        :param name: name of the parameter, eg "taxes.some_tax.some_param"
        :param data: Data loaded from a YAML file. In case of a reform, the data can also be created dynamically.

        .. py:attribute:: values_list

           List of the values, in anti-chronological order
    """

    _data_type = dict

    def __init__(self, name, data, file_path = None):
        self.name = name
        self.file_path = file_path

        self.validate(data)

        instants = sorted(data.keys(), reverse = True)  # sort by antechronological order

        values_list = []
        for instant_str in instants:
            if not INSTANT_PATTERN.match(instant_str):
                raise ParameterParsingError(
                    "Invalid property '{}' in '{}'. Properties must be valid YYYY-MM-DD instants, such as 2017-01-15."
                    .format(instant_str, self.name).encode('utf-8'),
                    file_path)

            instant_info = data[instant_str]

            #  Ignore expected values, as they are just metadata
            if instant_info == "expected" or isinstance(instant_info, dict) and instant_info.get("expected"):
                continue

            value_name = _compose_name(name, instant_str)
            value_at_instant = ValueAtInstant(value_name, instant_str, data = instant_info, file_path = file_path)
            values_list.append(value_at_instant)

        self.values_list = values_list

    def __repr__(self):
        return os.linesep.join([
            'ValuesHistory "{}"'.format(self.name),
            os.linesep.join([
                '  {}: {}'.format(value.instant_str, value.value) for value in self.values_list
                ])
            ])

    def __eq__(self, other):
        return (self.name == other.name) and (self.values_list == other.values_list)

    def _get_at_instant(self, instant_str):
        for value_at_instant in self.values_list:
            if value_at_instant.instant_str <= instant_str:
                return value_at_instant.value
        return None

    def update(self, period = None, start = None, stop = None, value = None):
        """Change the value for a given period.

        :param period: Period where the value is modified. If set, `start` and `stop` should be `None`.
        :param start: Start of the period. Instance of `openfisca_core.periods.Instant`. If set, `period` should be `None`.
        :param stop: Stop of the period. Instance of `openfisca_core.periods.Instant`. If set, `period` should be `None`.
        :param value: New value. If `None`, the parameter is removed from the legislation parameters for the given period.
        """
        if period is not None:
            if start is not None and stop is not None:
                raise ValueError(u"period parameter can't be used with start and stop")
            start = period.start
            stop = period.stop
        if start is None:
            raise ValueError("You must provide either a start or a period")
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
                    value_name = _compose_name(self.name, stop_str)
                    new_interval = ValueAtInstant(value_name, stop_str, data = {'value': overlapped_value})
                    new_values.append(new_interval)
                else:
                    value_name = _compose_name(self.name, stop_str)
                    new_interval = ValueAtInstant(value_name, stop_str, data = {'value': None})
                    new_values.append(new_interval)

        # Insert new interval
        value_name = _compose_name(self.name, start_str)
        new_interval = ValueAtInstant(value_name, start_str, data = {'value': value})
        new_values.append(new_interval)

        # Remove covered intervals
        while (i < n) and (old_values[i].instant_str >= start_str):
            i += 1

        # Past intervals : not affected
        while i < n:
            new_values.append(old_values[i])
            i += 1

        self.values_list = new_values


class Parameter(AbstractParameter):
    """
        A parameter of the legislation.
    """
    allowed_keys = set(['values', 'description', 'unit', 'reference'])

    def __init__(self, name, data, file_path = None):
        """
            :param name: name of the parameter, e.g. "taxes.some_tax.some_param"
            :param data: Data loaded from a YAML file.
            :param file_path: File the parameter was loaded from.
        """
        self.name = name
        self.file_path = file_path
        self.validate(data)
        self.description = data.get('description')

        values = data['values']
        self.values_history = ValuesHistory(name, data = values, file_path = file_path)

    def _get_at_instant(self, instant_str):
        return self.values_history._get_at_instant(instant_str)

    def update(self, **args):
        return self.values_history.update(**args)


class Bracket(AbstractParameter):
    """
        A scale bracket.
    """
    allowed_keys = set(['amount', 'threshold', 'rate', 'average_rate', 'base'])
    _data_type = dict

    def __init__(self, name, data = None, file_path = None):
        """
        :param name: name of the bracket, eg "taxes.some_scale.bracket_3"
        :param data: Data loaded from a YAML file. In case of a reform, the data can also be created dynamically.
        :param file_path: File the parameter was loaded from.
        """
        self.name = name
        self.file_path = file_path
        self.validate(data)

        for key, value in data.items():
            new_child_name = _compose_name(name, key)
            new_child = ValuesHistory(new_child_name, value, file_path)
            setattr(self, key, new_child)

    def _get_at_instant(self, instant_str):
        return BracketAtInstant(self.name, self, instant_str)


class BracketAtInstant(AbstractParameter):
    """
        A scale bracket at a given instant.
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


class Scale(AbstractParameter):
    """
        A parameter scale (for instance a  marginal scale).
    """
    allowed_keys = set(['brackets', 'description', 'unit', 'reference'])

    def __init__(self, name, data, file_path):
        """
        :param name: name of the scale, eg "taxes.some_scale"
        :param data: Data loaded from a YAML file. In case of a reform, the data can also be created dynamically.
        :param file_path: File the parameter was loaded from.
        """
        self.name = name
        self.file_path = file_path
        self.validate(data)
        self.description = data.get('description')

        if not isinstance(data['brackets'], list):
            raise ParameterParsingError(
                "Property 'brackets' of scale '{}' must be of type array."
                .format(self.name).encode('utf-8'),
                self.file_path
                )

        brackets = []
        for i, bracket_data in enumerate(data['brackets']):
            bracket_name = _compose_name(name, i)
            bracket = Bracket(bracket_name, bracket_data, file_path)
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


def _parse_child(child_name, child, child_path):
    if 'values' in child:
        return Parameter(child_name, child, child_path)
    elif 'brackets' in child:
        return Scale(child_name, child, child_path)
    else:
        return ParameterNode(child_name, data = child, file_path = child_path)


class ParameterNode(AbstractParameter):
    """
        A node in the legislation `parameter tree <http://openfisca.org/doc/coding-the-legislation/legislation_parameters.html>`_.
    """
    _data_type = dict

    def __init__(self, name = "", directory_path = None, data = None, file_path = None):
        """
        Instanciate a ParameterNode either from a dict, (using `data`), or from a directory containing YAML files (using `directory_path`).

        :param string name: Name of the node, eg "taxes.some_tax".
        :param string directory_path: Directory containing YAML files describing the node.
        :param string data: Object representing the parameter node. It usually has been extracted from a YAML file.
        :param string file_path: YAML file from which the `data` has been extracted from.
        """
        self.name = name

        if directory_path:
            self.children = {}
            for child_name in os.listdir(directory_path):
                child_path = os.path.join(directory_path, child_name)
                if os.path.isfile(child_path):
                    child_name, ext = os.path.splitext(child_name)
                    # We ignore non-YAML files, and index.yaml files, curently used to store metadatas
                    if ext not in PARAM_FILE_EXTENSIONS or child_name == 'index':
                        continue

                    child_name_expanded = _compose_name(name, child_name)
                    child = load_parameter_file(child_path, child_name_expanded)
                    self.children[child_name] = child
                    setattr(self, child_name, child)

                elif os.path.isdir(child_path):
                    child_name = os.path.basename(child_path)
                    child_name_expanded = _compose_name(name, child_name)
                    child = ParameterNode(child_name_expanded, directory_path = child_path)
                    self.children[child_name] = child
                    setattr(self, child_name, child)

        else:
            self.file_path = file_path
            self.validate(data)
            self.children = {}
            # We allow to set a reference and a description for a node. It is however not recommanded, as it's only metadata and is not exposed in the legislation explorer.
            data.pop('reference', None)
            data.pop('description', None)
            for child_name, child in data.items():
                child_name_expanded = _compose_name(name, child_name)
                child = _parse_child(child_name_expanded, child, file_path)
                self.children[child_name] = child
                setattr(self, child_name, child)

    def _get_at_instant(self, instant_str):
        return ParameterNodeAtInstant(self.name, self, instant_str)

    def merge(self, other):
        """
        Merges another ParameterNode into the current node.

        In case of child name conflict, the other node child will replace the current node child.
        """
        for child_name, child in other.children.items():
            self.children[child_name] = child

    def add_child(self, name, child):
        """
        Add a new child to the node.

        :param name: Name of the child that must be used to access that child. Should not contain anything that could interfere with the operator `.` (dot).
        :param child: The new child, an instance of :any:`Scale` or :any:`Parameter` or :any:`ParameterNode`.
        """
        if name in self.children:
            raise ValueError("{} has already a child named {}".format(self.name, name)).encode('utf-8')
        if not (isinstance(child, ParameterNode) or isinstance(child, Parameter) or isinstance(child, Scale)):
            raise TypeError("child must be of type ParameterNode, Parameter, or Scale. Instead got {}".format(type(child)).encode('utf-8'))
        self.children[name] = child
        setattr(self, name, child)


def load_parameter_file(file_path, name = ''):
    """
    Load parameters from a YAML file (or a directory containing YAML files).

    :returns: An instance of :any:`ParameterNode` or :any:`Scale` or :any:`Parameter`.
    """

    if not os.path.exists(file_path):
        raise ValueError("{} doest not exist".format(file_path).encode('utf-8'))
    if os.path.isdir(file_path):
        return ParameterNode(name, directory_path = file_path)

    with open(file_path, 'r') as f:
        try:
            data = yaml.load(f, Loader = Loader)
        except (yaml.scanner.ScannerError, yaml.parser.ParserError):
            stack_trace = traceback.format_exc()
            raise ParameterParsingError(
                "Invalid YAML. Check the traceback above for more details.",
                file_path,
                stack_trace
                )

    return _parse_child(name, data, file_path)


class ParameterNodeAtInstant(object):
    """
        Parameter node of the legislation, at a given instant.
    """
    def __init__(self, name, node, instant_str):
        """
        :param name: Name of the node.
        :param node: Original :any:`ParameterNode` instance.
        :param instant_str: A date in the format `YYYY-MM-DD`.
        """

        # The "technical" attributes are hidden, so that the node children can be easily browsed with auto-completion without pollution
        self._name = name
        self._instant_str = instant_str
        self._children = {}
        for child_name, child in node.children.items():
            child_at_instant = child._get_at_instant(instant_str)
            if child_at_instant is not None:
                self._children[child_name] = child_at_instant
                setattr(self, child_name, child_at_instant)

    def __getattr__(self, key):
        param_name = _compose_name(self._name, key)
        raise ParameterNotFound(param_name, self._instant_str)

    def __getitem__(self, key):  # deprecated
        return getattr(self, key)

    def __iter__(self):
        return iter(self._children)


def _compose_name(path, child_name):
    if path:
        if isinstance(child_name, int)or INSTANT_PATTERN.match(child_name):
            return '{}[{}]'.format(path, child_name)
        return '{}.{}'.format(path, child_name)
    else:
        return child_name
