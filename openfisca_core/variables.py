# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
import datetime
import inspect
import re
import textwrap

import numpy as np
from sortedcontainers.sorteddict import SortedDict
from datetime import date

from openfisca_core import entities
from openfisca_core import periods
from openfisca_core.indexed_enums import Enum, ENUM_ARRAY_DTYPE
from openfisca_core.periods import MONTH, YEAR, ETERNITY
from openfisca_core.base_functions import (
    missing_value,
    requested_period_default_value,
    requested_period_last_or_next_value,
    requested_period_last_value,
    )
from openfisca_core.commons import basestring_type, to_unicode


VALUE_TYPES = {
    bool: {
        'dtype': np.bool,
        'default': False,
        'json_type': 'boolean',
        'formatted_value_type': 'Boolean',
        'is_period_size_independent': True
        },
    int: {
        'dtype': np.int32,
        'default': 0,
        'json_type': 'integer',
        'formatted_value_type': 'Int',
        'is_period_size_independent': False
        },
    float: {
        'dtype': np.float32,
        'default': 0,
        'json_type': 'number',
        'formatted_value_type': 'Float',
        'is_period_size_independent': False,
        },
    str: {
        'dtype': object,
        'default': '',
        'json_type': 'string',
        'formatted_value_type': 'String',
        'is_period_size_independent': True
        },
    Enum: {
        'dtype': ENUM_ARRAY_DTYPE,
        'json_type': 'string',
        'formatted_value_type': 'String',
        'is_period_size_independent': True,
        },
    date: {
        'dtype': 'datetime64[D]',
        'default': datetime.date.fromtimestamp(0),  # 0 == 1970-01-01
        'json_type': 'string',
        'formatted_value_type': 'Date',
        'is_period_size_independent': True,
        },
    }


FORMULA_NAME_PREFIX = 'formula'


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

       .. py:attribute:: formulas

           Formulas used to calculate the variable

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

       .. py:attribute:: documentation

           Free multilines text field describing the variable context and usage.
    """

    def __init__(self, baseline_variable = None):
        self.name = to_unicode(self.__class__.__name__)
        attr = {
            name: value for name, value in self.__class__.__dict__.items()
            if not name.startswith('__')}
        self.baseline_variable = baseline_variable
        self.value_type = self.set(attr, 'value_type', required = True, allowed_values = VALUE_TYPES.keys())
        self.dtype = VALUE_TYPES[self.value_type]['dtype']
        self.json_type = VALUE_TYPES[self.value_type]['json_type']
        if self.value_type == Enum:
            self.possible_values = self.set(attr, 'possible_values', required = True, setter = self.set_possible_values)
        if self.value_type == str:
            self.max_length = self.set(attr, 'max_length', allowed_type = int)
            if self.max_length:
                self.dtype = '|S{}'.format(self.max_length)
        if self.value_type == Enum:
            self.default_value = self.set(attr, 'default_value', allowed_type = self.possible_values, required = True)
        else:
            self.default_value = self.set(attr, 'default_value', allowed_type = self.value_type, default = VALUE_TYPES[self.value_type].get('default'))
        self.entity = self.set(attr, 'entity', required = True, setter = self.set_entity)
        self.definition_period = self.set(attr, 'definition_period', required = True, allowed_values = (MONTH, YEAR, ETERNITY))
        self.label = self.set(attr, 'label', allowed_type = basestring_type, setter = self.set_label)
        self.end = self.set(attr, 'end', allowed_type = basestring_type, setter = self.set_end)
        self.reference = self.set(attr, 'reference', setter = self.set_reference)
        self.cerfa_field = self.set(attr, 'cerfa_field', allowed_type = (basestring_type, dict))
        self.unit = self.set(attr, 'unit', allowed_type = basestring_type)
        self.documentation = self.set(attr, 'documentation', allowed_type = basestring_type, setter = self.set_documentation)
        self.set_input = self.set_set_input(attr.pop('set_input', None))
        self.calculate_output = self.set_calculate_output(attr.pop('calculate_output', None))
        self.is_period_size_independent = self.set(attr, 'is_period_size_independent', allowed_type = bool, default = VALUE_TYPES[self.value_type]['is_period_size_independent'])
        self.base_function = self.set_base_function(attr.pop('base_function', None))

        formulas_attr, unexpected_attrs = _partition(attr, lambda name, value: name.startswith(FORMULA_NAME_PREFIX))
        self.formulas = self.set_formulas(formulas_attr)

        if unexpected_attrs:
            raise ValueError(
                'Unexpected attributes in definition of variable "{}": {!r}'
                .format(self.name, ', '.join(sorted(unexpected_attrs.keys()))))

        self.is_neutralized = False

    # ----- Setters used to build the variable ----- #

    def set(self, attributes, attribute_name, required = False, allowed_values = None, allowed_type = None, setter = None, default = None):
        value = attributes.pop(attribute_name, None)
        if value is None and self.baseline_variable:
            return getattr(self.baseline_variable, attribute_name)
        if required and value is None:
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

    def set_possible_values(self, possible_values):
        if not issubclass(possible_values, Enum):
            raise ValueError("Invalid value '{}' for attribute 'possible_values' in variable '{}'. Must be a subclass of {}."
            .format(possible_values, self.name, Enum).encode('utf-8'))
        return possible_values

    def set_label(self, label):
        if label:
            return to_unicode(label)

    def set_end(self, end):
        if end:
            try:
                return datetime.datetime.strptime(end, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError("Incorrect 'end' attribute format in '{}'. 'YYYY-MM-DD' expected where YYYY, MM and DD are year, month and day. Found: {}".format(self.name, end).encode('utf-8'))

    def set_reference(self, reference):
        if reference:
            if isinstance(reference, basestring_type):
                reference = [to_unicode(reference)]
            elif isinstance(reference, list):
                pass
            elif isinstance(reference, tuple):
                reference = list(reference)
            else:
                raise TypeError('The reference of the variable {} is a {} instead of a String or a List of Strings.'.format(self.name, type(reference)))

            for element in reference:
                if not isinstance(element, basestring_type):
                    raise TypeError(
                        'The reference of the variable {} is a {} instead of a String or a List of Strings.'.format(
                            self.name, type(reference)))

        return reference

    def set_documentation(self, documentation):
        if documentation:
            return textwrap.dedent(documentation)

    def set_base_function(self, base_function):
        if not base_function and self.baseline_variable:
            return self.baseline_variable.base_function

        if base_function and base_function not in {
                missing_value,
                requested_period_default_value,
                requested_period_last_or_next_value,
                requested_period_last_value
                }:
            raise ValueError('Unexpected base_function {}'.format(base_function).encode('utf-8'))

        if self.is_period_size_independent and base_function is None:
            return requested_period_last_value

        return base_function

    def set_set_input(self, set_input):
        if not set_input and self.baseline_variable:
            return self.baseline_variable.set_input
        return set_input

    def set_calculate_output(self, calculate_output):
        if not calculate_output and self.baseline_variable:
            return self.baseline_variable.calculate_output
        return calculate_output

    def set_formulas(self, formulas_attr):
        formulas = SortedDict()
        for formula_name, formula in formulas_attr.items():
            starting_date = self.parse_formula_name(formula_name)

            if self.end is not None and starting_date > self.end:
                raise ValueError('You declared that "{}" ends on "{}", but you wrote a formula to calculate it from "{}" ({}). The "end" attribute of a variable must be posterior to the start dates of all its formulas.'
                    .format(self.name, self.end, starting_date, formula_name).encode('utf-8'))

            formulas[str(starting_date)] = formula

        # If the variable is reforming a baseline variable, keep the formulas from the latter when they are not overridden by new formulas.
        if self.baseline_variable is not None:
            first_reform_formula_date = formulas.peekitem(0)[0] if formulas else None
            formulas.update({
                baseline_start_date: baseline_formula
                for baseline_start_date, baseline_formula in self.baseline_variable.formulas.items()
                if first_reform_formula_date is None or baseline_start_date < first_reform_formula_date
                })

        return formulas

    def parse_formula_name(self, attribute_name):
        """
        Returns the starting date of a formula based on its name.

        Valid dated name formats are : 'formula', 'formula_YYYY', 'formula_YYYY_MM' and 'formula_YYYY_MM_DD' where YYYY, MM and DD are a year, month and day.

        By convention, the starting date of:
            - `formula` is `0001-01-01` (minimal date in Python)
            - `formula_YYYY` is `YYYY-01-01`
            - `formula_YYYY_MM` is `YYYY-MM-01`
        """

        def raise_error():
            raise ValueError(
                'Unrecognized formula name in variable "{}". Expecting "formula_YYYY" or "formula_YYYY_MM" or "formula_YYYY_MM_DD where YYYY, MM and DD are year, month and day. Found: "{}".'
                .format(self.name, attribute_name).encode('utf-8'))

        if attribute_name == FORMULA_NAME_PREFIX:
            return date.min

        FORMULA_REGEX = r'formula_(\d{4})(?:_(\d{2}))?(?:_(\d{2}))?$'  # YYYY or YYYY_MM or YYYY_MM_DD

        match = re.match(FORMULA_REGEX, attribute_name)
        if not match:
            raise_error()
        date_str = '-'.join([match.group(1), match.group(2) or '01', match.group(3) or '01'])

        try:
            return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:  # formula_2005_99_99 for instance
            raise_error()

    # ----- Methods ----- #

    def is_input_variable(self):
        """
            Returns True if the variable is an input variable.
        """
        return len(self.formulas) == 0

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
            # Python 2 backward compatibility
            if isinstance(source_lines[0], bytes):
                source_lines = [source_line.decode('utf-8') for source_line in source_lines]
            source_code = textwrap.dedent(''.join(source_lines))
        except (IOError, TypeError):
            source_code, start_line_number = None, None

        return comments, to_unicode(source_file_path), to_unicode(source_code), start_line_number

    def get_formula(self, period = None):
        """
        Returns the formula used to compute the variable at the given period.

        If no period is given and the variable has several formula, return the oldest formula.

        :returns: Formula used to compute the variable
        :rtype: function
        """

        if not self.formulas:
            return None

        if period is None:
            return self.formulas.peekitem(index = 0)[1]  # peekitem gets the 1st key-value tuple (the oldest start_date and formula). Return the formula.

        if isinstance(period, periods.Period):
            instant = period.start
        else:
            try:
                instant = periods.period(period).start
            except ValueError:
                instant = periods.instant(period)

        if self.end and instant.date > self.end:
            return None

        instant = str(instant)
        for start_date in reversed(self.formulas):
            if start_date <= instant:
                return self.formulas[start_date]

        return None

    def clone(self):
        clone = self.__class__()
        return clone


def _partition(dict, predicate):
    true_dict = {}
    false_dict = {}

    for key, value in dict.items():
        if predicate(key, value):
            true_dict[key] = value
        else:
            false_dict[key] = value

    return true_dict, false_dict


def get_neutralized_variable(variable):
    """
        Return a new neutralized variable (to be used by reforms).
        A neutralized variable always returns its default value, and does not cache anything.
    """
    result = variable.clone()
    result.is_neutralized = True
    result.label = '[Neutralized]' if variable.label is None else '[Neutralized] {}'.format(variable.label),

    return result
