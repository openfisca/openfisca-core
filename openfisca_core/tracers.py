# -*- coding: utf-8 -*-


class Tracer(object):

    def __init__(self):
        self.requested_calculations = set()
        self.stack = []
        self.trace = {}
        self._computation_log = []

    @staticmethod
    def _get_key(variable_name, period, **parameters):
        if parameters.get('extra_params'):
            return u"{}<{}><{}>".format(variable_name, period, '><'.join(map(str, parameters['extra_params']))).encode('utf-8')
        return u"{}<{}>".format(variable_name, period).encode('utf-8')

    def start(self, variable_name, period, **parameters):
        """
            Record that OpenFisca started computing a variable.
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

    def stop(self, variable_name, period, result, **parameters):
        """
            Record that OpenFisca finished computing a variable.
        """
        key = self._get_key(variable_name, period, **parameters)
        expected_key = self.stack.pop()

        if not key == expected_key:
            raise ValueError(
                u"Something went wrong with the simulation tracer: result of '{0}' was expected, got results for '{1}' instead. This does not make sense as the last variable we started computing was '{0}'."
                .format(expected_key, key).encode('utf-8')
                )
        self.trace[key]['value'] = result.tolist()  # Cast numpy array into a python list

    def print_computation_log(self):
        for node, depth in self._computation_log:
            value = self.trace[node]['value']
            print("{}{} >> {}".format('  ' * depth, node, value))
