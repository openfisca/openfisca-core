# -*- coding: utf-8 -*-

class Tracer(object):

    def __init__(self):
        self.trace = {}
        self.stack = [('#/trace', self.trace)]
        self.computed_variables = {}

    @staticmethod
    def _get_key(variable_name, period, **parameters):
        if parameters.get('extra_params'):
            return u"{}<{}><{}>".format(variable_name, period, '><'.join(map(str, parameters['extra_params']))).encode('utf-8')
        return u"{}<{}>".format(variable_name, period).encode('utf-8')

    def start(self, variable_name, period, **parameters):
        key = self._get_key(variable_name, period, **parameters)
        path, current = self.stack[-1]
        next_path = '/'.join([path, key, 'dependencies'])
        if current.get(key):
            # Ignore variables which have already been computed, for instance if the same variable is requested for 2 persons
            next_node = None
        elif self.computed_variables.get(key):
            next_node = None
            current[key] = { '$ref': self.computed_variables[key]}
        else:
            current[key] = {'dependencies' : {}}
            self.computed_variables[key] = next_path.rstrip('/dependencies')
            next_node = current[key]['dependencies']
        self.stack.append((next_path, next_node))

    def stop(self, variable_name, period, result, **parameters):
        key = self._get_key(variable_name, period, **parameters)
        path = self.stack[-1][0]
        expected_key = path.rsplit('/', 2)[1]

        if not key == expected_key:
            raise ValueError(
                u"Something went wrong with the simulation tracer: result of '{0}' was expected, got results for '{1}' instead. This does not make sense as the last variable we started computing was '{0}'."
                .format(expected_key, key).encode('utf-8')
                )
        self.stack.pop()
        parent_node = self.stack[-1][1]
        # Don't rewrite the value if it already exists, or if the node is a reference to another node.
        if not parent_node[key].get('value') and not parent_node[key].get('$ref'):
            parent_node[key]['value'] = result.tolist()

