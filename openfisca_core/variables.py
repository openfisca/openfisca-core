# -*- coding: utf-8 -*-


import inspect
import textwrap
import datetime

import columns
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


class Variable(object):

    def __init__(self, baseline_variable = None):
        self.name = unicode(self.__class__.__name__)
        attributes = dict(self.__class__.__dict__)
        self.column = self.set_column(attributes.pop('column', None))
        self.default = self.column.default
        self.entity = self.set_entity(attributes.pop('entity', None))
        self.definition_period = self.set_definition_period(attributes.pop('definition_period', None))
        self.label = self.set_label(attributes.pop('label', None))
        self.end = self.set_end(attributes.pop('end', None))
        self.reference = self.set_reference(attributes.pop('reference', None))
        self.cerfa_field = self.set_cerfa_field(attributes.pop('cerfa_field', None))
        self.set_input = attributes.pop('set_input', None)
        self.calculate_output = attributes.pop('calculate_output', None)
        self.base_function = self.set_base_function(attributes.pop('calculate_output', None))
        self.formula = Formula.build_formula_class(attributes, self, baseline_variable)

        # Fill column attributes. To remove when we merge Columns and variables.
        if self.cerfa_field is not None:
            self.column.cerfa_field = self.cerfa_field
        if self.default != self.column.default:
            self.column.default = self.default
        if self.end is not None:
            self.column.end = self.end
        if self.reference is not None:
            self.column.reference = self.reference
        self.column.entity = self.entity
        self.column.formula_class = self.formula
        self.column.definition_period = self.definition_period
        self.column.is_neutralized = False
        self.column.label = self.label
        self.column.name = self.name


        # self.variable_class = variable_class


    def set_column(self, column):
        if not column:
            raise ValueError("Missing attribute 'column' in definition of variable {}".format(self.name).encode('utf-8'))
        if isinstance(column, type) and issubclass(column, columns.Column):
            return column()
        if isinstance(column, columns.Column):
            return column
        else:
            raise ValueError("Attribute 'column' invalid in '{}'".format(self.name).encode('utf-8'))

    def set_entity(self, entity):
        if not entity:
            raise ValueError("Missing attribute 'entity' in definition of variable {}".format(self.name).encode('utf-8'))
        if isinstance(entity, type) and issubclass(entity, entities.Entity):
            return entity
        else:
            raise ValueError("Attribute 'entity' invalid in '{}'".format(self.name).encode('utf-8'))

    def set_definition_period(self, definition_period):
        if not definition_period:
            raise ValueError("Missing attribute 'definition_period' in definition of variable {}".format(self.name).encode('utf-8'))
        if definition_period not in (MONTH, YEAR, ETERNITY):
            raise ValueError(u'Incorrect definition_period ({}) in {}'.format(definition_period, name).encode('utf-8'))

        return definition_period

    def set_label(self, label):
        if label:
            return unicode(label)

    def set_end(self, end):
        if end:
            assert isinstance(end, str), 'Type error on {}. String expected. Found: {}'.format(self.name + '.end', type(end))
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

    def set_cerfa_field(self, cerfa_field):
        if cerfa_field:
            assert isinstance(cerfa_field, (basestring, dict)), cerfa_field

    def set_base_function(self, base_function):
        if self.definition_period == ETERNITY:
            if base_function and not base_function == permanent_default_value:
                raise ValueError('Unexpected base_function {}'.format(base_function))
            return permanent_default_value

        if self.column.is_period_size_independent:
            if base_function is None:
                return requested_period_last_value
            if base_function in [missing_value, requested_period_last_value, requested_period_last_or_next_value]:
                return base_function
            raise ValueError('Unexpected base_function {}'.format(base_function))

        if base_function is None:
            return requested_period_default_value

        return base_function

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

        return comments, source_file_path.decode('utf-8'), source_code.decode('utf-8'), start_line_number.decode('utf-8')
