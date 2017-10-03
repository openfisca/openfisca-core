# -*- coding: utf-8 -*-

class Tracer(object):

    def __init__(self):
        self.trace = {}
        self.stack = [self.trace]
        self.computed_variables = {}

    def start(self, variable_name, period):
        key = "{}<{}>".format(variable_name, period).encode('utf-8')
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

    def stop(self, variable_name, period, result):
        self.stack.pop()  # Get out of dependencies
        current = self.stack[-1]
        current['value'] = result.tolist()
        self.stack.pop()  # Get out of current node

