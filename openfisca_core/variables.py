# -*- coding: utf-8 -*-


import inspect
import textwrap
import datetime

import numpy as np

import entities
from formulas import Formula
from periods import MONTH, YEAR, ETERNITY
from base_functions import (
    missing_value,
    permanent_default_value,
    requested_period_default_value,
    requested_period_last_or_next_value,
    requested_period_last_value,
    )
from enumerations import Enum
from datetime import date

VALUE_TYPES = {
    bool: {
        'dtype': np.bool,
        'default': False,
        'json_type': 'Boolean',
        'is_period_size_independent': True
        },
    int: {
        'dtype': np.int32,
        'default': 0,
        'json_type': 'Integer',
        'is_period_size_independent': False
        },
    float: {
        'dtype': np.float32,
        'default': 0,
        'json_type': 'Float',
        'is_period_size_independent': False,
        },
    str: {
        'dtype': object,
        'default': u'',
        'json_type': 'String',
        'is_period_size_independent': True
        },
    Enum: {
        'dtype': np.int16,
        'default': 0,
        'json_type': 'Enumeration',
        'is_period_size_independent': True,
        },
    date: {
        'dtype': 'datetime64[D]',
        'default': datetime.date.fromtimestamp(0),  # 0 == 1970-01-01
        'json_type': 'Date',
        'is_period_size_independent': True,
        },
    }


class Variable(object):

    def __init__(self, baseline_variable = None):
        self.name = unicode(self.__class__.__name__)
        attributes = dict(self.__class__.__dict__)
        self.baseline_variable = baseline_variable
        self.value_type = self.set_value_type(attributes.pop('value_type', None))
        self.dtype = VALUE_TYPES[self.value_type]['dtype']
        self.json_type = VALUE_TYPES[self.value_type]['json_type']
        if self.value_type == Enum:
            self.possible_values = self.set_possible_values(attributes.pop('possible_values', None))
        if self.value_type == str:
            self.max_length = attributes.pop('max_length', None)
            if self.max_length:
                self.dtype = '|S{}'.format(self.max_length)
        self.default = self.set_default(attributes.pop('default', None))
        self.entity = self.set_entity(attributes.pop('entity', None))
        self.definition_period = self.set_definition_period(attributes.pop('definition_period', None))
        self.label = self.set_label(attributes.pop('label', None))
        self.end = self.set_end(attributes.pop('end', None))
        self.reference = self.set_reference(attributes.pop('reference', None))
        self.cerfa_field = self.set_cerfa_field(attributes.pop('cerfa_field', None))
        self.set_input = self.set_set_input(attributes.pop('set_input', None))
        self.calculate_output = self.set_calculate_output(attributes.pop('calculate_output', None))
        self.is_period_size_independent = self.set_is_period_size_independent(attributes.pop('is_period_size_independent', None))
        self.base_function = self.set_base_function(attributes.pop('base_function', None))
        self.formula = Formula.build_formula_class(attributes, self, baseline_variable)
        self.is_neutralized = False

    def set_value_type(self, value_type):
        if not value_type and self.baseline_variable:
            return self.baseline_variable.value_type
        if not value_type:
            raise ValueError("Missing attribute 'value_type' in definition of variable {}".format(self.name).encode('utf-8'))
        if value_type in VALUE_TYPES:
            return value_type
        else:
            raise ValueError("Attribute 'value_type' invalid in '{}'".format(self.name).encode('utf-8'))

    def set_possible_values(self, possible_values):
        if not possible_values:
            raise ValueError("'possible_values' need to be set in {}, as its value type is 'Enum'".format(self.name).encode('utf-8'))
        return possible_values

    def set_default(self, default):
        if not default and self.baseline_variable:
            return self.baseline_variable.default
        if not default:
            return VALUE_TYPES[self.value_type]['default']
        return default

    def set_entity(self, entity):
        if not entity and self.baseline_variable:
            return self.baseline_variable.entity
        if not entity:
            raise ValueError("Missing attribute 'entity' in definition of variable {}".format(self.name).encode('utf-8'))
        if isinstance(entity, type) and issubclass(entity, entities.Entity):
            return entity
        else:
            raise ValueError("Attribute 'entity' invalid in '{}'".format(self.name).encode('utf-8'))

    def set_definition_period(self, definition_period):
        if not definition_period and self.baseline_variable:
            return self.baseline_variable.definition_period
        if not definition_period:
            raise ValueError("Missing attribute 'definition_period' in definition of variable {}".format(self.name).encode('utf-8'))
        if definition_period not in (MONTH, YEAR, ETERNITY):
            raise ValueError(u'Incorrect definition_period ({}) in {}'.format(definition_period, self.name).encode('utf-8'))

        return definition_period

    def set_label(self, label):
        if not label and self.baseline_variable:
            return self.baseline_variable.label
        if label:
            return unicode(label)

    def set_end(self, end):
        if not end and self.baseline_variable:
            return self.baseline_variable.end
        if end:
            assert isinstance(end, str), 'Type error on {}. String expected. Found: {}'.format(self.name + '.end', type(end))
            try:
                return datetime.datetime.strptime(end, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError(u"Incorrect 'end' attribute format in '{}'. 'YYYY-MM-DD' expected where YYYY, MM and DD are year, month and day. Found: {}".format(self.name, end).encode('utf-8'))

    def set_reference(self, reference):
        if not reference and self.baseline_variable:
            return self.baseline_variable.reference
        if reference:
            if isinstance(reference, basestring):
                reference = [reference]
            elif isinstance(reference, list):
                pass
            elif isinstance(reference, tuple):
                reference = list(reference)
            else:
                raise TypeError('The reference of the variable {} is a {} instead of a String or a List of Strings.'.format(self.name, type(reference)))

            for element in reference:
                if not isinstance(element, basestring):
                    raise TypeError(
                        'The reference of the variable {} is a {} instead of a String or a List of Strings.'.format(
                            self.name, type(reference)))

        return reference

    def set_cerfa_field(self, cerfa_field):
        if not cerfa_field and self.baseline_variable:
            return self.baseline_variable.cerfa_field
        if cerfa_field:
            assert isinstance(cerfa_field, (basestring, dict)), cerfa_field

    def set_is_period_size_independent(self, is_period_size_independent):
        if is_period_size_independent is None and self.baseline_variable:
            return self.baseline_variable.is_period_size_independent
        if is_period_size_independent is not None:
            return is_period_size_independent
        else:
            return VALUE_TYPES[self.value_type]['is_period_size_independent']

    def set_base_function(self, base_function):
        if not base_function and self.baseline_variable:
            return self.baseline_variable.formula.base_function.im_func
        if self.definition_period == ETERNITY:
            if base_function and not base_function == permanent_default_value:
                raise ValueError('Unexpected base_function {}'.format(base_function))
            return permanent_default_value

        if self.is_period_size_independent:
            if base_function is None:
                return requested_period_last_value
            if base_function in [missing_value, requested_period_last_value, requested_period_last_or_next_value]:
                return base_function
            raise ValueError('Unexpected base_function {}'.format(base_function))

        if base_function is None:
            return requested_period_default_value

        return base_function

    def set_set_input(self, set_input):
        if not set_input and self.baseline_variable:
            return self.baseline_variable.formula.set_input.im_func
        return set_input

    def set_calculate_output(self, calculate_output):
        if not calculate_output and self.baseline_variable:
            return self.baseline_variable.formula.calculate_output.im_func
        return calculate_output

    def is_input_variable(self):
        """Returns true if the variable is an input variable."""
        return self.formula.dated_formulas_class == []

    @classmethod
    def get_introspection_data(cls, tax_benefit_system):
        comments = inspect.getcomments(cls)

        # Handle dynamically generated variable classes or Jupyter Notebooks, which have no source.
        try:
            absolute_file_path = inspect.getsourcefile(cls)
        except TypeError:
            source_file_path = None
        else:
            source_file_path = absolute_file_path.replace(tax_benefit_system.get_package_metadata()['location'], '')
        try:
            source_lines, start_line_number = inspect.getsourcelines(cls)
            source_code = textwrap.dedent(''.join(source_lines))
        except (IOError, TypeError):
            source_code, start_line_number = None, None

        return comments, source_file_path.decode('utf-8'), source_code.decode('utf-8'), start_line_number

    def clone(self):
        clone = self.__class__()
        clone.formula = type(self.formula.__name__, self.formula.__bases__, dict(self.formula.__dict__))  # Class clone
        return clone
