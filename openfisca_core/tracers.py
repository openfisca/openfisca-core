# -*- coding: utf-8 -*-

class Tracer(object):

    def __init__(self):
        self.trace = {}
        self.stack = [self.trace]
        self.degub_stack = []
        self.computed_variables = {}

    def start(self, variable_name, period):
        key = "{}<{}>".format(variable_name, period).encode('utf-8')
        if key in self.degub_stack:
            pass # should not happen
        current = self.stack[-1]
        if current.get(key):
            pass  # Ignore variables which have already been computed, for instance if the same variable is requested for 2 persons
        elif self.computed_variables.get(key):
            current[key] = self.computed_variables[key]
        else:
            current[key] = {'dependencies' : {}}
            self.computed_variables[key] = current[key]
        self.stack.append(current[key])
        self.stack.append(current[key]['dependencies'])
        self.degub_stack.append(key)

    def stop(self, variable_name, period, result):
        key = "{}<{}>".format(variable_name, period).encode('utf-8')
        if not key == self.degub_stack[-1]:
            raise ValueError(
                "Something went wrong with the simulation tracer: result of {0} was expected, got results for {1} instead. This does not make sense as computation of {0} started before computation of {1}."
                .format(self.degub_stack[-1], key).encode('utf-8')
                )
        self.stack.pop()  # Get out of dependencies
        current = self.stack[-1]
        current['value'] = result.tolist()
        self.stack.pop()  # Get out of current node
        self.degub_stack.pop()

