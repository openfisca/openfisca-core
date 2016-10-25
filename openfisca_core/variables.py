# -*- coding: utf-8 -*-


import inspect
import textwrap

from openfisca_core.formulas import SimpleFormula, DatedFormula, EntityToPerson, PersonToEntity, new_filled_column
from openfisca_core import columns


class AbstractVariable(object):
    def __init__(self, name, attributes, variable_class):
        self.name = name
        self.attributes = attributes
        self.variable_class = variable_class

    def get_introspection_data(self, tax_benefit_system):
        comments = inspect.getcomments(self.variable_class)

        # Handle dynamically generated variable classes or Jupyter Notebooks, which have no source.
        try:
            source_file_path = inspect.getsourcefile(self.variable_class)
        except TypeError:
            source_file_path = None
        try:
            source_lines, start_line_number = inspect.getsourcelines(self.variable_class)
            source_code = textwrap.dedent(''.join(source_lines))
        except (IOError, TypeError):
            source_code, start_line_number = None, None

        return comments, source_file_path, source_code, start_line_number


class AbstractComputationVariable(AbstractVariable):
    formula_class = None  # Overridden

    def to_column(self, tax_benefit_system):
        entity_class = self.attributes.pop('entity_class', None)

        # For reform variable that replaces the existing reference one
        reference = self.attributes.pop('reference', None)
        if reference and not entity_class:
            entity_class = reference.entity_class

        comments, source_file_path, source_code, start_line_number = self.get_introspection_data(tax_benefit_system)

        if entity_class is None:
            raise Exception('Variable {} must have an entity_class'.format(self.name))

        return new_filled_column(
            name = self.name,
            entity_class = entity_class,
            formula_class = self.formula_class,
            reference_column = reference,
            comments = comments,
            start_line_number = start_line_number,
            source_code = source_code,
            source_file_path = source_file_path,
            **self.attributes
            )


class Variable(AbstractComputationVariable):
    formula_class = SimpleFormula


class DatedVariable(AbstractComputationVariable):
    formula_class = DatedFormula
