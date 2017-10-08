# -*- coding: utf-8 -*-

import logging

log = logging.getLogger(__name__)


class Tracer(object):
    """
        A tracer that records simulation steps to enable exploring calculation steps in details.

        .. py:attribute:: requested_calculations

            ``set`` containing calculations that have been directly requested by the client.

            Value example:

            >>> {'income_tax<2017-01>', 'basic_income<2017-01>'}

        .. py:attribute:: stack

            ``list`` of the calculations that have started, but have not finished. The first item is one of the :attr:`requested_calculations`, and each other item is a dependency of the one preceding him. Note that after a calculation is finished, :attr:`stack` is always `[]``.

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

    """
    def __init__(self):
        log.warn("The tracer is a feature that is still currently under experimentation. You are very welcome to use it and send us precious feedback, but keep in mind that the way it is used and the results it gives might change without any major version bump.")
        self.requested_calculations = set()
        self.stack = []
        self.trace = {}
        self._computation_log = []

    @staticmethod
    def _get_key(variable_name, period, **parameters):
        if parameters.get('extra_params'):
            return u"{}<{}><{}>".format(variable_name, period, '><'.join(map(str, parameters['extra_params']))).encode('utf-8')
        return u"{}<{}>".format(variable_name, period).encode('utf-8')

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
                u"Something went wrong with the simulation tracer: result of '{0}' was expected, got results for '{1}' instead. This does not make sense as the last variable we started computing was '{0}'."
                .format(expected_key, key).encode('utf-8')
                )
        self.trace[key]['value'] = result.tolist()  # Cast numpy array into a python list

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
                u"Something went wrong with the simulation tracer: calculation of '{1}' was aborted, whereas the last variable we started computing was '{0}'."
                .format(expected_key, key).encode('utf-8')
                )

        self._computation_log.pop()
        if self.stack:
            parent = self.stack[-1]
            self.trace[parent]['dependencies'].remove(key)
        del self.trace[key]

    def print_computation_log(self):
        """
            Print the computation log of a simulation
        """
        for node, depth in self._computation_log:
            value = self.trace[node]['value']
            print("{}{} >> {}".format('  ' * depth, node, value))
