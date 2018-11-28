# -*- coding: utf-8 -*-


"""Handle legislative parameters."""
from __future__ import unicode_literals, print_function, division, absolute_import


import os
import sys
import logging
import traceback

import yaml
import numpy as np

from openfisca_core import taxscales
from openfisca_core import periods
from openfisca_core.indexed_enums import Enum, EnumArray
from openfisca_core.periods import INSTANT_PATTERN
from openfisca_core.tools import indent
from openfisca_core.commons import basestring_type, empty_clone

log = logging.getLogger(__name__)

try:
    from yaml import CLoader as Loader
except ImportError:
    log.warning(
        "libyaml is not installed in your environment. This can make OpenFisca slower to start. Once you have installed libyaml, run 'pip uninstall pyyaml && pip install pyyaml --no-cache-dir' so that it is used in your Python environment." + os.linesep)
    from yaml import Loader


FILE_EXTENSIONS = {'.yaml', '.yml'}

# 'unit' and 'reference' are only listed here for backward compatibility.
#  It is now recommended to include them in metadata, until a common consensus emerges.
COMMON_KEYS = {'description', 'metadata', 'unit', 'reference', 'documentation'}
ALLOWED_PARAM_TYPES = (float, int, bool, type(None))


def date_constructor(loader, node):
    return node.value


yaml.add_constructor('tag:yaml.org,2002:timestamp', date_constructor, Loader = Loader)


class ParameterNotFound(AttributeError):
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
        message = "The parameter '{}'".format(name)
        if variable_name is not None:
            message += " requested by variable '{}'".format(variable_name)
        message += (
            " was not found in the {} tax and benefit system."
            ).format(instant_str)
        super(ParameterNotFound, self).__init__(message.encode('utf-8'))


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
            message = os.linesep.join([
                "Error parsing parameter file '{}':".format(file),
                message
                ])
        if traceback is not None:
            message = os.linesep.join([traceback, message]).encode('utf-8')
        super(ParameterParsingError, self).__init__(message)


class Parameter(object):
    """
        A parameter of the legislation. Parameters can change over time.

        :param string name: Name of the parameter, e.g. "taxes.some_tax.some_param"
        :param dict data: Data loaded from a YAML file.
        :param string file_path: File the parameter was loaded from.
        :param string documentation: Documentation describing parameter usage and context.


        Instantiate a parameter without metadata:

        >>>  Parameter('rate', data = {
                "2015-01-01": 550,
                "2016-01-01": 600
                })

        Instantiate a parameter with metadata:

        >>>  Parameter('rate', data = {
                'description': 'Income tax rate applied on salaries',
                'values': {
                    "2015-01-01": {'value': 550, 'metadata': {'reference': 'http://taxes.gov/income_tax/2015'}},
                    "2016-01-01": {'value': 600, 'metadata': {'reference': 'http://taxes.gov/income_tax/2016'}}
                    }
                })

        .. py:attribute:: values_list

           List of the values, in reverse chronological order
    """

    def __init__(self, name, data, file_path = None):
        self.name = name
        self.file_path = file_path
        _validate_parameter(self, data, data_type = dict)
        self.description = None
        self.metadata = {}
        self.documentation = None
        self.values_history = self  # Only for backward compatibility

        # Normal parameter declaration: the values are declared under the 'values' key: parse the description and metadata.
        if data.get('values'):
            # 'unit' and 'reference' are only listed here for backward compatibility
            _validate_parameter(self, data, allowed_keys = COMMON_KEYS.union({'values'}))
            self.description = data.get('description')

            _set_backward_compatibility_metadata(self, data)
            self.metadata.update(data.get('metadata', {}))

            _validate_parameter(self, data['values'], data_type = dict)
            values = data['values']

            self.documentation = data.get('documentation')

        else:  # Simplified parameter declaration: only values are provided
            values = data

        instants = sorted(values.keys(), reverse = True)  # sort in reverse chronological order

        values_list = []
        for instant_str in instants:
            if not INSTANT_PATTERN.match(instant_str):
                raise ParameterParsingError(
                    "Invalid property '{}' in '{}'. Properties must be valid YYYY-MM-DD instants, such as 2017-01-15."
                    .format(instant_str, self.name),
                    file_path)

            instant_info = values[instant_str]

            #  Ignore expected values, as they are just metadata
            if instant_info == "expected" or isinstance(instant_info, dict) and instant_info.get("expected"):
                continue

            value_name = _compose_name(name, item_name = instant_str)
            value_at_instant = ParameterAtInstant(value_name, instant_str, data = instant_info, file_path = self.file_path, metadata = self.metadata)
            values_list.append(value_at_instant)

        self.values_list = values_list

    def __repr__(self):
        return os.linesep.join([
            '{}: {}'.format(value.instant_str, value.value if value.value is not None else 'null') for value in self.values_list
            ])

    def __eq__(self, other):
        return (self.name == other.name) and (self.values_list == other.values_list)

    def __call__(self, instant):
        return self.get_at_instant(instant)

    def get_at_instant(self, instant):
        instant = str(periods.instant(instant))
        return self._get_at_instant(instant)

    def _get_at_instant(self, instant):
        for value_at_instant in self.values_list:
            if value_at_instant.instant_str <= instant:
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
            if start is not None or stop is not None:
                raise TypeError("Wrong input for 'update' method: use either 'update(period, value = value)' or 'update(start = start, stop = stop, value = value)'. You cannot both use 'period' and 'start' or 'stop'.")
            if isinstance(period, basestring_type):
                period = periods.period(period)
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
                    value_name = _compose_name(self.name, item_name = stop_str)
                    new_interval = ParameterAtInstant(value_name, stop_str, data = {'value': overlapped_value})
                    new_values.append(new_interval)
                else:
                    value_name = _compose_name(self.name, item_name = stop_str)
                    new_interval = ParameterAtInstant(value_name, stop_str, data = {'value': None})
                    new_values.append(new_interval)

        # Insert new interval
        value_name = _compose_name(self.name, item_name = start_str)
        new_interval = ParameterAtInstant(value_name, start_str, data = {'value': value})
        new_values.append(new_interval)

        # Remove covered intervals
        while (i < n) and (old_values[i].instant_str >= start_str):
            i += 1

        # Past intervals : not affected
        while i < n:
            new_values.append(old_values[i])
            i += 1

        self.values_list = new_values

    def get_descendants(self):
        return iter(())


class ParameterAtInstant(object):
    """
        A value of a parameter at a given instant.
    """

    # 'unit' and 'reference' are only listed here for backward compatibility
    _allowed_keys = set(['value', 'metadata', 'unit', 'reference'])

    def __init__(self, name, instant_str, data = None, file_path = None, metadata = None):
        """
            :param string name: name of the parameter, e.g. "taxes.some_tax.some_param"
            :param string instant_str: Date of the value in the format `YYYY-MM-DD`.
            :param dict data: Data, usually loaded from a YAML file.
        """
        self.name = name
        self.instant_str = instant_str
        self.file_path = file_path
        self.metadata = {}

        # Accept { 2015-01-01: 4000 }
        if not isinstance(data, dict) and isinstance(data, ALLOWED_PARAM_TYPES):
            self.value = data
            return

        self.validate(data)
        self.value = data['value']

        if metadata is not None:
            self.metadata.update(metadata)  # Inherit metadata from Parameter
        _set_backward_compatibility_metadata(self, data)
        self.metadata.update(data.get('metadata', {}))

    def validate(self, data):
        _validate_parameter(self, data, data_type = dict, allowed_keys = self._allowed_keys)
        try:
            value = data['value']
        except KeyError:
            raise ParameterParsingError(
                "Missing 'value' property for {}".format(self.name),
                self.file_path
                )
        if not isinstance(value, ALLOWED_PARAM_TYPES):
            raise ParameterParsingError(
                "Invalid value in {} : {}".format(self.name, value),
                self.file_path
                )

    def __eq__(self, other):
        return (self.name == other.name) and (self.instant_str == other.instant_str) and (self.value == other.value)

    def __repr__(self):
        result = "ParameterAtInstant({})".format({self.instant_str: self.value})
        # repr output must be encoded in Python 2, but not in Python 3
        if sys.version_info < (3, 0):
            return result.encode('utf-8')
        return result


class ParameterNode(object):
    """
        A node in the legislation `parameter tree <https://openfisca.org/doc/coding-the-legislation/legislation_parameters.html>`_.
    """

    _allowed_keys = None  # By default, no restriction on the keys

    def __init__(self, name = "", directory_path = None, data = None, file_path = None):
        """
        Instantiate a ParameterNode either from a dict, (using `data`), or from a directory containing YAML files (using `directory_path`).

        :param string name: Name of the node, eg "taxes.some_tax".
        :param string directory_path: Directory containing YAML files describing the node.
        :param dict data: Object representing the parameter node. It usually has been extracted from a YAML file.
        :param string file_path: YAML file from which the `data` has been extracted from.


        Instantiate a ParameterNode from a dict:

        >>> node = ParameterNode('basic_income', data = {
            'amount': {
              'values': {
                "2015-01-01": {'value': 550},
                "2016-01-01": {'value': 600}
                }
              },
            'min_age': {
              'values': {
                "2015-01-01": {'value': 25},
                "2016-01-01": {'value': 18}
                }
              },
            })

        Instantiate a ParameterNode from a directory containing YAML parameter files:

        >>> node = ParameterNode('benefits', directory_path = '/path/to/country_package/parameters/benefits')
        """
        self.name = name
        self.children = {}
        self.description = None
        self.documentation = None
        self.file_path = None
        self.metadata = {}

        if directory_path:
            self.file_path = directory_path
            for child_name in os.listdir(directory_path):
                child_path = os.path.join(directory_path, child_name)
                if os.path.isfile(child_path):
                    child_name, ext = os.path.splitext(child_name)

                    # We ignore non-YAML files
                    if ext not in FILE_EXTENSIONS:
                        continue

                    if child_name == 'index':
                        data = _load_yaml_file(child_path) or {}
                        _validate_parameter(self, data, allowed_keys = COMMON_KEYS)
                        self.description = data.get('description')
                        self.documentation = data.get('documentation')
                        _set_backward_compatibility_metadata(self, data)
                        self.metadata.update(data.get('metadata', {}))
                    else:
                        child_name_expanded = _compose_name(name, child_name)
                        child = load_parameter_file(child_path, child_name_expanded)
                        self.add_child(child_name, child)

                elif os.path.isdir(child_path):
                    child_name = os.path.basename(child_path)
                    child_name_expanded = _compose_name(name, child_name)
                    child = ParameterNode(child_name_expanded, directory_path = child_path)
                    self.add_child(child_name, child)

        else:
            self.file_path = file_path
            _validate_parameter(self, data, data_type = dict, allowed_keys = self._allowed_keys)
            self.description = data.get('description')
            self.documentation = data.get('documentation')
            _set_backward_compatibility_metadata(self, data)
            self.metadata.update(data.get('metadata', {}))
            for child_name, child in data.items():
                if child_name in COMMON_KEYS:
                    continue  # do not treat reserved keys as subparameters.

                child_name = str(child_name)
                child_name_expanded = _compose_name(name, child_name)
                child = _parse_child(child_name_expanded, child, file_path)
                self.add_child(child_name, child)

    def __call__(self, instant):
        return self.get_at_instant(instant)

    def get_at_instant(self, instant):
        instant = str(periods.instant(instant))
        return self._get_at_instant(instant)

    def _get_at_instant(self, instant):
        return ParameterNodeAtInstant(self.name, self, instant)

    def merge(self, other):
        """
        Merges another ParameterNode into the current node.

        In case of child name conflict, the other node child will replace the current node child.
        """
        for child_name, child in other.children.items():
            self.add_child(child_name, child)

    def add_child(self, name, child):
        """
        Add a new child to the node.

        :param name: Name of the child that must be used to access that child. Should not contain anything that could interfere with the operator `.` (dot).
        :param child: The new child, an instance of :any:`Scale` or :any:`Parameter` or :any:`ParameterNode`.
        """
        if name in self.children:
            raise ValueError("{} has already a child named {}".format(self.name, name).encode('utf-8'))
        if not (isinstance(child, ParameterNode) or isinstance(child, Parameter) or isinstance(child, Scale)):
            raise TypeError("child must be of type ParameterNode, Parameter, or Scale. Instead got {}".format(type(child)).encode('utf-8'))
        self.children[name] = child
        setattr(self, name, child)

    def __repr__(self):
        result = os.linesep.join(
            [os.linesep.join(
                ["{}:", "{}"]).format(name, indent(repr(value)))
                for name, value in sorted(self.children.items())]
            )
        # repr output must be encoded in Python 2, but not in Python 3
        if sys.version_info < (3, 0):
            return result.encode('utf-8')
        return result

    def get_descendants(self):
        """
            Return a generator containing all the parameters and nodes recursively contained in this `ParameterNode`
        """
        for child in self.children.values():
            yield child
            for descendant in child.get_descendants():  # would be `yield from child.walk()` in Python 3.
                yield descendant

    def clone(self):
        new = empty_clone(self)
        new_dict = new.__dict__

        for key, value in self.__dict__.items():
            if key not in ('children', 'metadata'):
                new_dict[key] = value

        new_dict['children'] = self.children.copy()
        new_dict['metadata'] = self.metadata.copy()
        return new


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
                self.add_child(child_name, child_at_instant)

    def add_child(self, child_name, child_at_instant):
        self._children[child_name] = child_at_instant
        setattr(self, child_name, child_at_instant)

    def __getattr__(self, key):
        param_name = _compose_name(self._name, item_name = key)
        raise ParameterNotFound(param_name, self._instant_str)

    def __getitem__(self, key):
        # If fancy indexing is used, cast to a vectorial node
        if isinstance(key, np.ndarray):
            return VectorialParameterNodeAtInstant.build_from_node(self)[key]
        return self._children[key]

    def __iter__(self):
        return iter(self._children)

    def __repr__(self):
        result = os.linesep.join(
            [os.linesep.join(
                ["{}:", "{}"]).format(name, indent(repr(value)))
                for name, value in self._children.items()]
            )
        if sys.version_info < (3, 0):
            return result.encode('utf-8')
        return result


class VectorialParameterNodeAtInstant(object):
    """
        Parameter node of the legislation at a given instant which has been vectorized.
        Vectorized parameters allow requests such as parameters.housing_benefit[zipcode], where zipcode is a vector
    """

    @staticmethod
    def build_from_node(node):
        VectorialParameterNodeAtInstant.check_node_vectorisable(node)
        subnodes_name = node._children.keys()
        # Recursively vectorize the children of the node
        vectorial_subnodes = tuple([
            VectorialParameterNodeAtInstant.build_from_node(node[subnode_name]).vector if isinstance(node[subnode_name], ParameterNodeAtInstant) else node[subnode_name]
            for subnode_name in subnodes_name
            ])
        # A vectorial node is a wrapper around a numpy recarray
        # We first build the recarray
        recarray = np.array(
            [vectorial_subnodes],
            dtype = [
                (subnode_name, subnode.dtype if isinstance(subnode, np.recarray) else 'float')
                for (subnode_name, subnode) in zip(subnodes_name, vectorial_subnodes)
                ]
            )

        return VectorialParameterNodeAtInstant(node._name, recarray.view(np.recarray), node._instant_str)

    @staticmethod
    def check_node_vectorisable(node):
        """
            Check that a node can be casted to a vectorial node, in order to be able to use fancy indexing.
        """
        MESSAGE_PART_1 = "Cannot use fancy indexing on parameter node '{}', as"
        MESSAGE_PART_3 = "To use fancy indexing on parameter node, its children must be homogenous."
        MESSAGE_PART_4 = "See more at <https://openfisca.org/doc/coding-the-legislation/legislation_parameters#computing-a-parameter-that-depends-on-a-variable-fancy-indexing>."

        def raise_key_inhomogeneity_error(node_with_key, node_without_key, missing_key):
            message = " ".join([
                MESSAGE_PART_1,
                "'{}' exists, but '{}' doesn't.",
                MESSAGE_PART_3,
                MESSAGE_PART_4,
                ]).format(
                node._name,
                '.'.join([node_with_key, missing_key]),
                '.'.join([node_without_key, missing_key]),
                ).encode('utf-8')

            raise ValueError(message)

        def raise_type_inhomogeneity_error(node_name, non_node_name):
            message = " ".join([
                MESSAGE_PART_1,
                "'{}' is a node, but '{}' is not.",
                MESSAGE_PART_3,
                MESSAGE_PART_4,
                ]).format(
                node._name,
                node_name,
                non_node_name,
                ).encode('utf-8')

            raise ValueError(message)

        def raise_not_implemented(node_name, node_type):
            message = " ".join([
                MESSAGE_PART_1,
                "'{}' is a '{}', and fancy indexing has not been implemented yet on this kind of parameters.",
                MESSAGE_PART_4,
                ]).format(
                node._name,
                node_name,
                node_type,
                ).encode('utf-8')
            raise NotImplementedError(message)

        def extract_named_children(node):
            return {
                '.'.join([node._name, key]): value
                for key, value in node._children.items()
                }

        def check_nodes_homogeneous(named_nodes):
            """
                Check than several nodes (or parameters, or baremes) have the same structure.
            """
            names = list(named_nodes.keys())
            nodes = list(named_nodes.values())
            first_node = nodes[0]
            first_name = names[0]
            if isinstance(first_node, ParameterNodeAtInstant):
                children = extract_named_children(first_node)
                for node, name in list(zip(nodes, names))[1:]:
                    if not isinstance(node, ParameterNodeAtInstant):
                        raise_type_inhomogeneity_error(first_name, name)
                    first_node_keys = first_node._children.keys()
                    node_keys = node._children.keys()
                    if not first_node_keys == node_keys:
                        missing_keys = set(first_node_keys).difference(node_keys)
                        if missing_keys:  # If the first_node has a key that node hasn't
                            raise_key_inhomogeneity_error(first_name, name, missing_keys.pop())
                        else:  # If If the node has a key that first_node doesn't have
                            missing_key = set(node_keys).difference(first_node_keys).pop()
                            raise_key_inhomogeneity_error(name, first_name, missing_key)
                    children.update(extract_named_children(node))
                check_nodes_homogeneous(children)
            elif isinstance(first_node, float) or isinstance(first_node, int):
                for node, name in list(zip(nodes, names))[1:]:
                    if isinstance(node, int) or isinstance(node, float):
                        pass
                    elif isinstance(node, ParameterNodeAtInstant):
                        raise_type_inhomogeneity_error(name, first_name)
                    else:
                        raise_not_implemented(name, type(node).__name__)

            else:
                raise_not_implemented(first_name, type(first_node).__name__)

        check_nodes_homogeneous(extract_named_children(node))

    def __init__(self, name, vector, instant_str):

        self.vector = vector
        self._name = name
        self._instant_str = instant_str

    def __getattr__(self, attribute):
        result = getattr(self.vector, attribute)
        if isinstance(result, np.recarray):
            return VectorialParameterNodeAtInstant(result)
        return result

    def __getitem__(self, key):
        # If the key is a string, just get the subnode
        if isinstance(key, basestring_type):
            return self.__getattr__(key)
        # If the key is a vector, e.g. ['zone_1', 'zone_2', 'zone_1']
        elif isinstance(key, np.ndarray):
            if not np.issubdtype(key.dtype, np.str_):
                # In case the key is not a string vector, stringify it
                if key.dtype == object and issubclass(type(key[0]), Enum):
                    enum = type(key[0])
                    key = np.select([key == item for item in enum], [item.name for item in enum])
                elif isinstance(key, EnumArray):
                    enum = key.possible_values
                    key = np.select([key == item.index for item in enum], [item.name for item in enum])
                else:
                    key = key.astype('str')
            names = list(self.dtype.names)  # Get all the names of the subnodes, e.g. ['zone_1', 'zone_2']
            default = np.full_like(self.vector[key[0]], np.nan)  # In case of unexpected key, we will set the corresponding value to NaN.
            conditions = [key == name for name in names]
            values = [self.vector[name] for name in names]
            result = np.select(conditions, values, default)
            if contains_nan(result):
                unexpected_key = set(key).difference(self.vector.dtype.names).pop()
                raise ParameterNotFound('.'.join([self._name, unexpected_key]), self._instant_str)

            # If the result is not a leaf, wrap the result in a vectorial node.
            if np.issubdtype(result.dtype, np.record):
                return VectorialParameterNodeAtInstant(self._name, result.view(np.recarray), self._instant_str)

            return result


class Scale(object):
    """
        A parameter scale (for instance a  marginal scale).
    """
    # 'unit' and 'reference' are only listed here for backward compatibility
    _allowed_keys = COMMON_KEYS.union({'brackets'})

    def __init__(self, name, data, file_path):
        """
        :param name: name of the scale, eg "taxes.some_scale"
        :param data: Data loaded from a YAML file. In case of a reform, the data can also be created dynamically.
        :param file_path: File the parameter was loaded from.
        """
        self.name = name
        self.file_path = file_path
        _validate_parameter(self, data, data_type = dict, allowed_keys = self._allowed_keys)
        self.description = data.get('description')
        self.metadata = {}
        _set_backward_compatibility_metadata(self, data)
        self.metadata.update(data.get('metadata', {}))

        if not isinstance(data['brackets'], list):
            raise ParameterParsingError(
                "Property 'brackets' of scale '{}' must be of type array."
                .format(self.name),
                self.file_path
                )

        brackets = []
        for i, bracket_data in enumerate(data['brackets']):
            bracket_name = _compose_name(name, item_name = i)
            bracket = Bracket(name = bracket_name, data = bracket_data, file_path = file_path)
            brackets.append(bracket)
        self.brackets = brackets

    def __call__(self, instant):
        return self.get_at_instant(instant)

    def get_at_instant(self, instant):
        instant = str(periods.instant(instant))
        return self._get_at_instant(instant)

    def _get_at_instant(self, instant):
        brackets = [bracket.get_at_instant(instant) for bracket in self.brackets]

        if any('amount' in bracket._children for bracket in brackets):
            scale = taxscales.AmountTaxScale()
            for bracket in brackets:
                if 'amount' in bracket._children and 'threshold' in bracket._children:
                    amount = bracket.amount
                    threshold = bracket.threshold
                    scale.add_bracket(threshold, amount)
            return scale
        elif any('average_rate' in bracket._children for bracket in brackets):
            scale = taxscales.LinearAverageRateTaxScale()

            for bracket in brackets:
                if 'base' in bracket._children:
                    base = bracket.base
                else:
                    base = 1.
                if 'average_rate' in bracket._children and 'threshold' in bracket._children:
                    average_rate = bracket.average_rate
                    threshold = bracket.threshold
                    scale.add_bracket(threshold, average_rate * base)
            return scale
        else:
            scale = taxscales.MarginalRateTaxScale()

            for bracket in brackets:
                if 'base' in bracket._children:
                    base = bracket.base
                else:
                    base = 1.
                if 'rate' in bracket._children and 'threshold' in bracket._children:
                    rate = bracket.rate
                    threshold = bracket.threshold
                    scale.add_bracket(threshold, rate * base)
            return scale

    def __getitem__(self, key):
        if isinstance(key, int) and key < len(self.brackets):
            return self.brackets[key]
        else:
            raise KeyError(key)

    def __repr__(self):
        return os.linesep.join(
            ['brackets:']
            + [indent('-' + indent(repr(bracket))[1:]) for bracket in self.brackets]
            )

    def get_descendants(self):
        return iter(())


class Bracket(ParameterNode):
    """
        A scale bracket.
    """
    _allowed_keys = set(['amount', 'threshold', 'rate', 'average_rate', 'base'])


def _load_yaml_file(file_path):
    with open(file_path, 'r') as f:
        try:
            return yaml.load(f, Loader = Loader)
        except (yaml.scanner.ScannerError, yaml.parser.ParserError):
            stack_trace = traceback.format_exc()
            raise ParameterParsingError(
                "Invalid YAML. Check the traceback above for more details.",
                file_path,
                stack_trace
                )


def load_parameter_file(file_path, name = ''):
    """
    Load parameters from a YAML file (or a directory containing YAML files).

    :returns: An instance of :any:`ParameterNode` or :any:`Scale` or :any:`Parameter`.
    """
    if not os.path.exists(file_path):
        raise ValueError("{} doest not exist".format(file_path).encode('utf-8'))
    if os.path.isdir(file_path):
        return ParameterNode(name, directory_path = file_path)
    data = _load_yaml_file(file_path)
    return _parse_child(name, data, file_path)


def _parse_child(child_name, child, child_path):
    if 'values' in child:
        return Parameter(child_name, child, child_path)
    elif 'brackets' in child:
        return Scale(child_name, child, child_path)
    elif isinstance(child, dict) and all([INSTANT_PATTERN.match(str(key)) for key in child.keys()]):
        return Parameter(child_name, child, child_path)
    else:
        return ParameterNode(child_name, data = child, file_path = child_path)


def _compose_name(path, child_name = None, item_name = None):
    if not path:
        return child_name
    if child_name is not None:
        return '{}.{}'.format(path, child_name)
    if item_name is not None:
        return '{}[{}]'.format(path, item_name)


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


def _set_backward_compatibility_metadata(parameter, data):
    if data.get('unit') is not None:
        parameter.metadata['unit'] = data['unit']
    if data.get('reference') is not None:
        parameter.metadata['reference'] = data['reference']


def contains_nan(vector):
    if np.issubdtype(vector.dtype, np.record):
        return any([contains_nan(vector[name]) for name in vector.dtype.names])
    else:
        return np.isnan(vector).any()


# Only for backward compatibility
class ValuesHistory(Parameter):
    pass
