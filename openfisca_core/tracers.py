# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import

import numpy as np

import logging
import copy
from collections import defaultdict

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
                'income_tax<2017-01': {
                  'dependencies':['global_income<2017-01>', 'nb_children<2017-01>']
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
    def _get_key(variable_name, period, **parameters):
        if parameters.get('extra_params'):
            return "{}<{}><{}>".format(variable_name, period, '><'.join(map(str, parameters['extra_params'])))
        return "{}<{}>".format(variable_name, period)

    def record_calculation_start(self, variable_name, period, **parameters):
        """
            Record that OpenFisca started computing a variable.

            :param str variable_name: Name of the variable starting to be computed
            :param Period period: Period for which the variable is being computed
            :param list parameters: Parameter with which the variable is being computed
        """
        key = self._get_key(variable_name, period, **parameters)

        if self.stack:  # The variable is a dependency of another variable
            parent = self.stack[-1]
            self.trace[parent]['dependencies'].append(key)
        else:  # The variable has been requested by the client
            self.requested_calculations.add(key)

        if not self.trace.get(key):
            self.trace[key] = {'dependencies': []}
        self.stack.append(key)
        self._computation_log.append((key, len(self.stack)))
        self.usage_stats[variable_name]['nb_requests'] += 1

    def record_calculation_end(self, variable_name, period, result, **parameters):
        """
            Record that OpenFisca finished computing a variable.

            :param str variable_name: Name of the variable starting to be computed
            :param Period period: Period for which the variable is being computed
            :param numpy.ndarray result: Result of the computation
            :param list parameters: Parameter with which the variable is being computed
        """
        key = self._get_key(variable_name, period, **parameters)
        expected_key = self.stack.pop()

        if not key == expected_key:
            raise ValueError(
                "Something went wrong with the simulation tracer: result of '{0}' was expected, got results for '{1}' instead. This does not make sense as the last variable we started computing was '{0}'."
                .format(expected_key, key).encode('utf-8')
                )
        self.trace[key]['value'] = result

    def record_calculation_abortion(self, variable_name, period, **parameters):
        """
            Record that OpenFisca aborted computing a variable. This removes all trace of this computation.

            :param str variable_name: Name of the variable starting to be computed
            :param Period period: Period for which the variable is being computed
            :param list parameters: Parameter with which the variable is being computed
        """
        key = self._get_key(variable_name, period, **parameters)
        expected_key = self.stack.pop()

        if not key == expected_key:
            raise ValueError(
                "Something went wrong with the simulation tracer: calculation of '{1}' was aborted, whereas the last variable we started computing was '{0}'."
                .format(expected_key, key).encode('utf-8')
                )

        if self.stack:
            parent = self.stack[-1]
            self.trace[parent]['dependencies'].remove(key)
        del self.trace[key]

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
            print("{}{} >> {}".format('  ' * depth, node, value))

        if not self.trace.get(key):
            return print_line(depth, key, "Calculation aborted due to a circular dependency")

        if not aggregate:
            return print_line(depth, key, self.trace[key]['value'])

        return print_line(depth, key, self._get_aggregate(key))

    def print_trace(self, variable_name, period, extra_params = None, max_depth = 1, aggregate = False, ignore_zero = False):
        """
            Print value, the dependencies, and the dependencies values of the variable for the given period (and possibly the given set of extra parameters).

            :param str variable_name: Name of the variable to investigate
            :param Period period: Period to investigate
            :param list extra_params: Set of extra parameters
            :param int max_depth: Maximum level of recursion
            :param bool aggregate: See :any:`print_computation_log`
            :param bool ignore_zero: If ``True``, don't print dependencies if their value is 0
        """
        key = self._get_key(variable_name, period, extra_params = extra_params)

        def _print_details(key, depth):
            if depth > 0 and ignore_zero and np.all(self.trace[key]['value'] == 0):
                return
            self._print_node(key, depth, aggregate)
            if depth < max_depth:
                for dependency in self.trace[key]['dependencies']:
                    _print_details(dependency, depth + 1)

        _print_details(key, 0)

    def print_computation_log(self, aggregate = False):
        """
            Print the computation log of a simulation.

            If ``aggregate`` is ``False`` (default), print the value of each computed vector.

            If ``aggregate`` is ``True``, only print the minimum, maximum, and average value of each computed vector.
            This mode is more suited for simulations on a large population.
        """
        for node, depth in self._computation_log:
            self._print_node(node, depth, aggregate)
