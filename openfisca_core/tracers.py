# -*- coding: utf-8 -*-

class Tracer(object):

    def __init__(self):
        self.stack = []
        self.trace = {}

    @staticmethod
    def _get_key(variable_name, period, **parameters):
        if parameters.get('extra_params'):
            return u"{}<{}><{}>".format(variable_name, period, '><'.join(map(str, parameters['extra_params']))).encode('utf-8')
        return u"{}<{}>".format(variable_name, period).encode('utf-8')

    def start(self, variable_name, period, **parameters):
        key = self._get_key(variable_name, period, **parameters)

        if self.stack:
            parent = self.stack[-1]
            self.trace[parent]['dependencies'].append(key)

        if not self.trace.get(key):
            self.trace[key] = {'dependencies' : []}
        self.stack.append(key)

    def stop(self, variable_name, period, result, **parameters):
        key = self._get_key(variable_name, period, **parameters)
        expected_key = self.stack.pop()

        if not key == expected_key:
            raise ValueError(
                u"Something went wrong with the simulation tracer: result of '{0}' was expected, got results for '{1}' instead. This does not make sense as the last variable we started computing was '{0}'."
                .format(expected_key, key).encode('utf-8')
                )
        self.trace[key]['value'] = result.tolist()
