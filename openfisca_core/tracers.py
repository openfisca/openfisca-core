# -*- coding: utf-8 -*-

import numpy as np

import logging
import copy
from collections import defaultdict
from typing import List

from openfisca_core.parameters import ParameterNodeAtInstant, VectorialParameterNodeAtInstant, ALLOWED_PARAM_TYPES
from openfisca_core.taxscales import AbstractTaxScale
from openfisca_core.indexed_enums import EnumArray

log = logging.getLogger(__name__)


class Tracer(object):
    """
        A tracer that records simulation steps to enable exploring calculation steps in details.

        .. py:attribute:: requested_calculations

            ``set`` containing calculations that have been directly requested by the client.

            Value example:

            >>> {'income_tax<2017-01>', 'basic_income<2017-01>'}

        .. py:attribute:: stack

            ``list`` of the calculations that have started, but have not finished. The first item is one of the :attr:`requested_calculations`, and each other item is a dependency of the one preceding him. Note that after a calculation is finished, :attr:`stack` is always ``[]``.

            Value example:

            >>> ['income_tax<2017-01>', 'global_income<2017-01>', 'salary<2017-01>']

        .. py:attribute:: trace

            ``dict`` containing, for each calculation, its result and its immediate dependencies.

            Value example:

            .. code-block:: python

              {
                'income_tax<2017-01>': {
                  'dependencies':['global_income<2017-01>', 'nb_children<2017-01>'],
                  'parameters' : {'taxes.income_tax_rate<2015-01>': 0.15, ...},
                  'value': 600
                  },
                'global_income<2017-01>': {...}
              }

        .. py:attribute:: usage_stats

            ``dict`` containing, for each variable computed, the number of times the variable was requested.

            Value example:

            .. code-block:: python

              {
                'salary': {
                  'nb_requests': 17
                  },
                'global_income': {
                  'nb_requests': 1
                  }
              }

    """

    def __init__(self):
        self.requested_calculations = set()
        self.stack = []
        self.trace = {}
        self.usage_stats = defaultdict(lambda: {"nb_requests": 0})
        self._computation_log = []
        self._aggregates = {}

    def clone(self):
        new = Tracer()
        new.requested_calculations = copy.copy(self.requested_calculations)
        new.stack = copy.copy(self.stack)
        new.trace = copy.deepcopy(self.trace)
        new._computation_log = copy.copy(self._computation_log)
        new.usage_stats = copy.deepcopy(self.usage_stats)
        new._aggregates = copy.deepcopy(self._aggregates)

        return new

    @staticmethod
    def _get_key(variable_name, period):
        return "{}<{}>".format(variable_name, period)

    def record_calculation_start(self, variable_name, period):
        """
            Record that OpenFisca started computing a variable.

            :param str variable_name: Name of the variable starting to be computed
            :param Period period: Period for which the variable is being computed
        """
        key = self._get_key(variable_name, period)

        if self.stack:  # The variable is a dependency of another variable
            parent = self.stack[-1]
            self.trace[parent]['dependencies'].append(key)
        else:  # The variable has been requested by the client
            self.requested_calculations.add(key)

        if not self.trace.get(key):
            self.trace[key] = {'dependencies': [], 'parameters': {}}

        self.stack.append(key)
        self._computation_log.append((key, len(self.stack)))
        self.usage_stats[variable_name]['nb_requests'] += 1

    def record_calculation_parameter_access(self, parameter_name, period, value):
        if isinstance(value, AbstractTaxScale):
            value = value.to_dict()
        if isinstance(value, np.ndarray):
            value = value.tolist()

        parent = self.stack[-1]
        parameter_key = '{}<{}>'.format(
            parameter_name,
            period
            )
        self.trace[parent]['parameters'][parameter_key] = value

    def record_calculation_end(self, variable_name, period, result):
        """
            Record that OpenFisca finished computing a variable.

            :param str variable_name: Name of the variable starting to be computed
            :param Period period: Period for which the variable is being computed
            :param numpy.ndarray result: Result of the computation
        """
        key = self._get_key(variable_name, period)
        expected_key = self.stack.pop()

        if not key == expected_key:
            raise ValueError(
                "Something went wrong with the simulation tracer: result of '{0}' was expected, got results for '{1}' instead. This does not make sense as the last variable we started computing was '{0}'."
                .format(expected_key, key)
                )
        self.trace[key]['value'] = result

    def _get_aggregate(self, key):
        if self._aggregates.get(key):
            return self._aggregates.get(key)

        value = self.trace[key]['value']
        try:
            aggregated_value = {
                'min': np.min(value),
                'max': np.max(value),
                }
        except TypeError:  # Much less efficient, but works for strings
            aggregated_value = {
                'min': min(value),
                'max': max(value),
                }
        try:
            aggregated_value['avg'] = np.mean(value)
        except TypeError:
            aggregated_value['avg'] = np.nan

        self._aggregates[key] = aggregated_value
        return aggregated_value

    def _print_node(self, key, depth, aggregate):

        def print_line(depth, node, value):
            if isinstance(value, EnumArray):
                value = value.decode_to_str()
            formatted = np.array2string(value, max_line_width=float("inf"))
            return "{}{} >> {}".format('  ' * depth, node, formatted)

        if not self.trace.get(key):
            return print_line(depth, key, "Calculation aborted due to a circular dependency")

        if not aggregate:
            return print_line(depth, key, self.trace[key]['value'])

        return print_line(depth, key, self._get_aggregate(key))

    def print_trace(self, variable_name, period, max_depth = 1, aggregate = False, ignore_zero = False):
        """
            Print value, the dependencies, and the dependencies values of the variable for the given period.

            :param str variable_name: Name of the variable to investigate
            :param Period period: Period to investigate
            :param int max_depth: Maximum level of recursion
            :param bool aggregate: See :any:`print_computation_log`
            :param bool ignore_zero: If ``True``, don't print dependencies if their value is 0
        """
        key = self._get_key(variable_name, period)

        def _print_details(key, depth):
            if depth > 0 and ignore_zero and np.all(self.trace[key]['value'] == 0):
                return
            yield self._print_node(key, depth, aggregate)
            if depth < max_depth:
                for dependency in self.trace[key]['dependencies']:
                    return _print_details(dependency, depth + 1)

        return _print_details(key, 0)

    def computation_log(self, aggregate = False):
        return [self._print_node(node, depth, aggregate) for node, depth in self._computation_log]

    def print_computation_log(self, aggregate = False):
        """
            Print the computation log of a simulation.

            If ``aggregate`` is ``False`` (default), print the value of each computed vector.

            If ``aggregate`` is ``True``, only print the minimum, maximum, and average value of each computed vector.
            This mode is more suited for simulations on a large population.
        """
        for line in self.computation_log(aggregate):
            print(line)  # noqa T001


class TracingParameterNodeAtInstant(object):

    def __init__(self, parameter_node_at_instant, tracer):
        self.parameter_node_at_instant = parameter_node_at_instant
        self.tracer = tracer

    def __getattr__(self, key):
        child = getattr(self.parameter_node_at_instant, key)
        return self.get_traced_child(child, key)

    def __getitem__(self, key):
        child = self.parameter_node_at_instant[key]
        return self.get_traced_child(child, key)

    def get_traced_child(self, child, key):
        period = self.parameter_node_at_instant._instant_str
        if isinstance(child, (ParameterNodeAtInstant, VectorialParameterNodeAtInstant)):
            return TracingParameterNodeAtInstant(child, self.tracer)
        if not isinstance(key, str) or isinstance(self.parameter_node_at_instant, VectorialParameterNodeAtInstant):
            # In case of vectorization, we keep the parent node name as, for instance, rate[status].zone1 is best described as the value of "rate"
            name = self.parameter_node_at_instant._name
        else:
            name = '.'.join([self.parameter_node_at_instant._name, key])
        if isinstance(child, (np.ndarray,) + ALLOWED_PARAM_TYPES):
            self.tracer.record_parameter_access(name, period, child)
        return child


class SimpleTracer:

    def __init__(self):
        self._stack = []

    @property
    def stack(self):
        return self._stack

    @stack.setter
    def stack(self, stack):
        self._stack = stack

    def enter_calculation(self, variable: str, period):
        self.stack.append({'name': variable, 'period': period})

    def record_calculation_result(self, value: np.ndarray):
        pass  # ignore calculation result

    def exit_calculation(self):
        self.stack.pop()


class FullTracer(SimpleTracer):

    def __init__(self):
        SimpleTracer.__init__(self)
        self._trees = []
        self._current_node = None

    @property
    def trees(self):
        return self._trees

    def enter_calculation(self, variable: str, period):
        new_node = {'name': variable, 'period': period, 'children': [], 'parameters': [], 'value': None}
        if self._current_node is None:
            self._trees.append(new_node)
        else:
            self._current_node['children'].append(new_node)
        self.stack.append(new_node)
        self._current_node = new_node


    def record_parameter_access(self, parameter: str, period, value):
        self._current_node['parameters'].append({'name': parameter, 'period': period, 'value': value})

    def record_calculation_result(self, value: np.ndarray):
        self._current_node['value'] = value

    def exit_calculation(self):
        SimpleTracer.exit_calculation(self)
        if self.stack == []:
            self._current_node = None
        else:
            self._current_node = self.stack[-1]

    def _get_nb_requests(self, tree, variable: str):
        tree_call = tree['name'] == variable
        children_calls = sum(self._get_nb_requests(child, variable) for child in tree['children'])

        return tree_call + children_calls

    def get_nb_requests(self, variable: str):
        return sum(self._get_nb_requests(tree, variable) for tree in self.trees)

    def _get_aggregate(self, node):
        pass

    def _get_node_log(self, node, depth, aggregate) -> List[str]:

        def print_line(depth, node) -> str:
            return "{}{}<{}> >> {}".format('  ' * depth, node['name'], node['period'], node['value'])

        # if not self.trace.get(node):
        #     return print_line(depth, node, "Calculation aborted due to a circular dependency")

        node_log = [print_line(depth, node)]
        children_logs = _flatten(
            self._get_node_log(child, depth + 1, aggregate)
            for child in node['children']
            )


        return node_log + children_logs

        # return [print_line(depth, node, self._get_aggregate(node))]


    def computation_log(self, aggregate = False) -> List[str]:
        depth = 1
        lines_by_tree =  [self._get_node_log(node, depth, aggregate) for node in self._trees]
        return _flatten(lines_by_tree)

    def print_computation_log(self, aggregate = False):
        """
            Print the computation log of a simulation.

            If ``aggregate`` is ``False`` (default), print the value of each computed vector.

            If ``aggregate`` is ``True``, only print the minimum, maximum, and average value of each computed vector.
            This mode is more suited for simulations on a large population.
        """
        for line in self.computation_log(aggregate):
            print(line)  # noqa T001


def _flatten(list_of_lists):
    return [item for _list in list_of_lists for item in _list]
