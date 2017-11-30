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
from datetime import date
from enum import Enum, EnumMeta

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
        'dtype': object,
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
    """

    A `variable <http://openfisca.org/doc/variables.html>`_ of the legislation.

    Main attributes:

       .. py:attribute: name

           Name of the variable

       .. py:attribute:: value_type

           The value type of the variable. Possible value types in OpenFisca are ``int`` ``float`` ``bool`` ``str`` ``date`` and ``Enum``.

       .. py:attribute:: entity

           `Entity <http://openfisca.org/doc/person,_entities,_role.html>`_ the variable is defined for. For instance : ``Person``, ``Household``.

       .. py:attribute:: definition_period

           `Period <http://openfisca.org/doc/coding-the-legislation/35_periods.html>`_ the variable is defined for. Possible value: ``MONTH``, ``YEAR``, ``ETERNITY``.

       .. py:attribute:: label

           Description of the variable

       .. py:attribute:: reference

           Legislative reference describing the variable.

       .. py:attribute:: default_value

           `Default value <http://openfisca.org/doc/variables.html#default-values>`_ of the variable.

    Secondary attributes:

       .. py:attribute:: baseline_variable

           If the variable has been introduced in a `reform <http://openfisca.org/doc/reforms.html>`_ to replace another variable, baseline_variable is the replaced variable.

       .. py:attribute:: dtype

           Numpy `dtype <https://docs.scipy.org/doc/numpy-1.13.0/reference/generated/numpy.dtype.html>`_ used under the hood for the variable.

       .. py:attribute:: end

           `Date <http://openfisca.org/doc/coding-the-legislation/40_legislation_evolutions.html#variable-end>`_  when the variable disappears from the legislation.

       .. py:attribute:: formula

           Formula used to calculate the variable

       .. py:attribute:: is_neutralized

           True if the variable is neutralized. Neutralized variables never use their formula, and only return their default values when calculated.

       .. py:attribute:: json_type

           JSON type corresponding to the variable.

       .. py:attribute:: max_length

           If the value type of the variable is ``str``, max length of the string allowed. ``None`` if there is no limit.

       .. py:attribute:: possible_values

           If the value type of the variable is ``Enum``, contains the values the variable can take.

       .. py:attribute:: set_input

           Function used to automatically process variable inputs defined for periods not matching the definition_period of the variable. See more on the `documentation <http://openfisca.org/doc/coding-the-legislation/35_periods.html#automatically-process-variable-inputs-defined-for-periods-not-matching-the-definitionperiod>`_. Possible values are ``set_input_dispatch_by_period``, ``set_input_divide_by_period``, or nothing.

       .. py:attribute:: unit

           Free text field describing the unit of the variable. Only used as metadata.
    """

    def __init__(self, baseline_variable = None):
        self.name = unicode(self.__class__.__name__)
        attr = dict(self.__class__.__dict__)
        self.baseline_variable = baseline_variable
        self.value_type = self.set(attr, 'value_type', required = True, allowed_values = VALUE_TYPES.keys())
        self.dtype = VALUE_TYPES[self.value_type]['dtype']
        self.json_type = VALUE_TYPES[self.value_type]['json_type']
        if self.value_type == Enum:
            self.possible_values = self.set(attr, 'possible_values', required = True, allowed_type = EnumMeta)
        if self.value_type == str:
            self.max_length = self.set(attr, 'max_length', allowed_type = int)
            if self.max_length:
                self.dtype = '|S{}'.format(self.max_length)
        default_type = self.possible_values if self.value_type == Enum else self.value_type
        self.default_value = self.set(attr, 'default_value', allowed_type = default_type, default = VALUE_TYPES[self.value_type].get('default'))
        self.entity = self.set(attr, 'entity', required = True, setter = self.set_entity)
        self.definition_period = self.set(attr, 'definition_period', required = True, allowed_values = (MONTH, YEAR, ETERNITY))
        self.label = self.set(attr, 'label', allowed_type = basestring, setter = self.set_label)
        self.end = self.set(attr, 'end', allowed_type = basestring, setter = self.set_end)
        self.reference = self.set(attr, 'reference', setter = self.set_reference)
        self.cerfa_field = self.set(attr, 'cerfa_field', allowed_type = (basestring, dict))
        self.unit = self.set(attr, 'unit', allowed_type = basestring)
        self.set_input = self.set_set_input(attr.pop('set_input', None))
        self.calculate_output = self.set_calculate_output(attr.pop('calculate_output', None))
        self.is_period_size_independent = self.set(attr, 'is_period_size_independent', allowed_type = bool, default = VALUE_TYPES[self.value_type]['is_period_size_independent'])
        self.base_function = self.set_base_function(attr.pop('base_function', None))
        self.formula = Formula.build_formula_class(attr, self, baseline_variable)
        self.is_neutralized = False

    def set(self, attributes, attribute_name, required = False, allowed_values = None, allowed_type = None, setter = None, default = None):
        value = attributes.pop(attribute_name, None)
        if value is None and self.baseline_variable:
            return getattr(self.baseline_variable, attribute_name)
        if required and not value:
            raise ValueError("Missing attribute '{}' in definition of variable '{}'.".format(attribute_name, self.name).encode('utf-8'))
        if allowed_values is not None and value not in allowed_values:
            raise ValueError("Invalid value '{}' for attribute '{}' in variable '{}'. Allowed values are '{}'."
                .format(value, attribute_name, self.name, allowed_values).encode('utf-8'))
        if allowed_type is not None and value is not None and not isinstance(value, allowed_type):
            if allowed_type == float and isinstance(value, int):
                value = float(value)
            else:
                raise ValueError("Invalid value '{}' for attribute '{}' in variable '{}'. Must be of type '{}'."
                    .format(value, attribute_name, self.name, allowed_type).encode('utf-8'))
        if setter is not None:
            value = setter(value)
        if value is None and default is not None:
            return default
        return value

    def set_entity(self, entity):
        if not isinstance(entity, type) or not issubclass(entity, entities.Entity):
            raise ValueError("Invalid value '{}' for attribute 'entity' in variable '{}'. Must be a subclass of Entity."
            .format(entity, self.name).encode('utf-8'))
        return entity

    def set_label(self, label):
        if label:
            return unicode(label)

    def set_end(self, end):
        if end:
            try:
                return datetime.datetime.strptime(end, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError(u"Incorrect 'end' attribute format in '{}'. 'YYYY-MM-DD' expected where YYYY, MM and DD are year, month and day. Found: {}".format(self.name, end).encode('utf-8'))

    def set_reference(self, reference):
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
        """
        Get instrospection data about the code of the variable.

        :returns: (comments, source file path, source code, start line number)
        :rtype: tuple

        """
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
