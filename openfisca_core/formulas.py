# -*- coding: utf-8 -*-


from __future__ import division

import collections
import inspect
import datetime
import logging
import warnings
from os import linesep

import numpy as np

from . import holders, periods
from .parameters import ParameterNotFound
from .periods import MONTH, YEAR, ETERNITY
from .commons import empty_clone, stringify_array
from .indexed_enums import Enum, EnumArray


log = logging.getLogger(__name__)


ADD = 'add'
DIVIDE = 'divide'



# Formulas


class Formula(object):
    """
    An OpenFisca Formula for a Variable.
    Such a Formula might have different behaviors according to the time period.
    """
    comments = None
    holder = None
    start_line_number = None
    source_code = None
    source_file_path = None
    base_function = None  # Class attribute. Overridden by subclasses
    dated_formulas = None  # A list of dictionaries containing a formula instance and a start instant
    dated_formulas_class = None  # A list of dictionaries containing a formula class and a start instant

    def __init__(self, holder = None):
        assert holder is not None
        self.holder = holder

        if self.dated_formulas_class is not None:
            self.dated_formulas = [
                dict(
                    formula = dated_formula_class['formula_class'](holder = holder),
                    start_instant = dated_formula_class['start_instant'],
                    )
                for dated_formula_class in self.dated_formulas_class
                ]

    def clone(self, holder, keys_to_skip = None):
        """Copy the formula just enough to be able to run a new simulation without modifying the original simulation."""
        new = empty_clone(self)
        new_dict = new.__dict__

        if keys_to_skip is None:
            keys_to_skip = set()
        keys_to_skip.add('dated_formulas')
        keys_to_skip.add('holder')

        for key, value in self.__dict__.iteritems():
            if key not in keys_to_skip:
                new_dict[key] = value
        new_dict['holder'] = holder

        if self.dated_formulas is not None:
            new.dated_formulas = [
                {
                    key: value.clone(holder) if key == 'formula' else value
                    for key, value in dated_formula.iteritems()
                    }
                for dated_formula in self.dated_formulas
                ]

        return new

    def calculate_output(self, period):
        return self.holder.compute(period).array

    def default_values(self):
        '''Return a new NumPy array which length is the entity count, filled with default values.'''
        return self.zeros() + self.holder.variable.default_value

    @property
    def real_formula(self):
        return self


    @classmethod
    def at_instant(cls, instant, default = UnboundLocalError):
        assert isinstance(instant, periods.Instant)
        for dated_formula_class in cls.dated_formulas_class:
            start_instant = dated_formula_class['start_instant']
            if (start_instant is None or start_instant <= instant):
                return dated_formula_class['formula_class']
        if default is UnboundLocalError:
            raise KeyError(instant)
        return default

    def find_function(self, period):
        """
        Finds the last active formula for the time interval [period starting date, variable end attribute].
        """
        end = self.holder.variable.end
        if end and period.start.date > end:
            return None

        # All formulas are already dated (with default start date in absence of user date)
        for dated_formula in reversed(self.dated_formulas):
            start = dated_formula['start_instant'].date

            if period.start.date >= start:
                return dated_formula['formula'].formula

        return None

    def exec_function(self, simulation, period, *extra_params):
        """
        Calls the right Variable's dated function for current period and returns a NumPy array.
        """

        function = self.find_function(period)
        entity = self.holder.entity
        function = function.im_func
        parameters_at = simulation.parameters_at
        if function.func_code.co_argcount == 2:
            return function(entity, period)
        else:
            return function(entity, period, parameters_at, *extra_params)

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


def get_neutralized_variable(variable):
    """
        Return a new neutralized variable (to be used by reforms).
        A neutralized variable always returns its default value, and does not cache anything.
    """
    result = variable.clone()
    result.is_neutralized = True
    result.label = u'[Neutralized]' if variable.label is None else u'[Neutralized] {}'.format(variable.label),
    result.set_input = set_input_neutralized
    result.formula.set_input = set_input_neutralized

    return result
