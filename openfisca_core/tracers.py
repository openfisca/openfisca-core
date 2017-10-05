# -*- coding: utf-8 -*-

class Tracer(object):

    def __init__(self):
        self.trace = {}
        self.stack = [('#', self.trace)]
        # self.computed_variables = {}

    @staticmethod
    def _get_key(variable_name, period):
        return "{}<{}>".format(variable_name, period).encode('utf-8')

    def start(self, variable_name, period):
        key = self._get_key(variable_name, period)
        path, current = self.stack[-1]
        if current.get(key):
            pass  # Ignore variables which have already been computed, for instance if the same variable is requested for 2 persons
        # elif self.computed_variables.get(key):
        #     current[key] = { "$ref": self.computed_variables[key]}
        else:
            current[key] = {'dependencies' : {}}
            # self.computed_variables[key] = current[key]
        self.stack.append(('/'.join([path, key]), current[key]['dependencies']))

    def stop(self, variable_name, period, result):
        key = self._get_key(variable_name, period)
        path = self.stack[-1][0]
        expected_key = path.rsplit('/', 1)[1]
        if not key == expected_key:
            raise ValueError(
                u"Something went wrong with the simulation tracer: result of '{0}' was expected, got results for '{1}' instead. This does not make sense as the last variable we started computing was '{0}'."
                .format(expected_key, key).encode('utf-8')
                )
        self.stack.pop()
        parent_node = self.stack[-1][1]
        parent_node[key]['value'] = result.tolist()

