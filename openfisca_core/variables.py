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


class AbstractConversionVariable(AbstractVariable):
    formula_class = None  # Overridden

    def to_column(self, tax_benefit_system):
        # Extract attributes.

        cerfa_field = self.attributes.pop('cerfa_field', None)
        if cerfa_field is not None:
            assert isinstance(cerfa_field, (basestring, dict)), cerfa_field

        __doc__ = self.attributes.pop('__doc__', None)
        __module__ = self.attributes.pop('__module__', None)

        entity_class = self.attributes.pop('entity_class')

        label = self.attributes.pop('label', None)
        label = self.name if label is None else unicode(label)

        law_reference = self.attributes.pop('law_reference', None)
        if law_reference is not None:
            assert isinstance(law_reference, (basestring, list))

        url = self.attributes.pop('url', None)
        if url is not None:
            url = unicode(url)

        reference_variable = self.attributes.pop('variable')
        reference_variable_name = unicode(reference_variable.__name__)
        reference_column = tax_benefit_system.get_column(reference_variable_name)

        if reference_column is None:
            reference_column = tax_benefit_system.add_variable(reference_variable)
            tax_benefit_system.automatically_loaded_variable.add(reference_variable_name)

        # Build formula class and column from extracted attributes.

        formula_class_attributes = {}
        if __doc__ is not None:
            formula_class_attributes['__doc__'] = __doc__
        if __module__ is not None:
            formula_class_attributes['__module__'] = __module__

        comments, source_file_path, source_code, start_line_number = self.get_introspection_data(tax_benefit_system)

        if comments is not None:
            if isinstance(comments, str):
                comments = comments.decode('utf-8')
            formula_class_attributes['comments'] = comments
        if source_file_path is not None:
            formula_class_attributes['source_file_path'] = source_file_path
        if source_code is not None:
            formula_class_attributes['source_code'] = source_code
        if start_line_number is not None:
            formula_class_attributes['start_line_number'] = start_line_number

        role = self.attributes.pop('role', None)
        roles = self.attributes.pop('roles', None)
        if role is None:
            if roles is not None:
                assert isinstance(roles, (list, tuple)) and all(isinstance(role, int) for role in roles)
        else:
            assert isinstance(role, int)
            assert roles is None
            roles = [role]
        if roles is not None:
            formula_class_attributes['roles'] = roles

        formula_class_attributes['variable_name'] = reference_column.name

        if issubclass(self.formula_class, EntityToPerson):
            assert entity_class.is_persons_entity
            column = reference_column.empty_clone()
        else:
            assert issubclass(self.formula_class, PersonToEntity)
            assert not entity_class.is_persons_entity

            if roles is None or len(roles) > 1:
                operation = self.attributes.pop('operation')
                assert operation in ('add', 'or'), 'Invalid operation: {}'.format(operation)
                formula_class_attributes['operation'] = operation

                if operation == 'add':
                    if reference_column.__class__ is columns.BoolCol:
                        column = columns.IntCol()
                    else:
                        column = reference_column.empty_clone()
                else:
                    assert operation == 'or'
                    column = reference_column.empty_clone()
            else:
                column = reference_column.empty_clone()

        # Ensure that all attributes defined in ConversionColumn class are used.
        assert not self.attributes, 'Unexpected attributes in definition of filled column "{}": {!r}'.format(
            self.name, self.attributes.keys())

        formula_class = type(self.name.encode('utf-8'), (self.formula_class,), formula_class_attributes)

        # Fill column attributes.
        if cerfa_field is not None:
            column.cerfa_field = cerfa_field
        if reference_column.end is not None:
            column.end = reference_column.end
        column.entity = entity_class.symbol  # Obsolete: To remove once build_..._couple() functions are no more used.
        column.entity_key_plural = entity_class.key_plural
        column.entity_class = entity_class
        column.formula_class = formula_class
        if reference_column.is_permanent:
            column.is_permanent = True
        column.label = label
        column.law_reference = law_reference
        column.name = self.name
        if reference_column.start is not None:
            column.start = reference_column.start
        if url is not None:
            column.url = url

        return column


class EntityToPersonColumn(AbstractConversionVariable):
    formula_class = EntityToPerson


class PersonToEntityColumn(AbstractConversionVariable):
    formula_class = PersonToEntity
