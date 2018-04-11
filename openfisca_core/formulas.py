# -*- coding: utf-8 -*-


from __future__ import division


def calculate_output(self, period):
    return self.holder.compute(period).array


def default_values(self):
    '''Return a new NumPy array which length is the entity count, filled with default values.'''
    return self.zeros() + self.holder.variable.default_value


@property
def real_formula(self):
    return self


def graph_parameters(self, edges, get_input_variables_and_parameters, nodes, visited):
    """Recursively build a graph of formulas."""
    if self.dated_formulas is not None:
        for dated_formula in self.dated_formulas:
            dated_formula['formula'].graph_parameters(edges, get_input_variables_and_parameters, nodes, visited)
    else:
        holder = self.holder
        variable = holder.variable
        simulation = holder.simulation
        variables_name, parameters_name = get_input_variables_and_parameters(variable)
        if variables_name is not None:
            for variable_name in sorted(variables_name):
                variable_holder = simulation.get_or_new_holder(variable_name)
                variable_holder.graph(edges, get_input_variables_and_parameters, nodes, visited)
                edges.append({
                    'from': variable_holder.variable.name,
                    'to': variable.name,
                    })


def calculate_output_add(formula, period):
    return formula.holder.compute_add(period).array


def calculate_output_divide(formula, period):
    return formula.holder.compute_divide(period).array
