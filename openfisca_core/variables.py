import inspect, textwrap
from openfisca_core.formulas import SimpleFormula, EntityToPerson, new_filled_column

class AbstractNewVariable():
    def __init__(self, name, attributes, variable_class):
        self.name = name
        self.attributes = { attr_name.strip('_'): attr_value for (attr_name, attr_value) in attributes.iteritems() }
        self.variable_class = variable_class

    def introspect(self):
        comments = inspect.getcomments(self.variable_class)

        # Handle dynamically generated variable classes or Jupyter Notebooks, which have no source.
        try:
            source_file_path = inspect.getsourcefile(self.variable_class)
        except TypeError:
            source_file_path = None
        try:
            source_lines, line_number = inspect.getsourcelines(self.variable_class)
            source_code = textwrap.dedent(''.join(source_lines))
        except (IOError, TypeError):
            source_code, line_number = None, None

        return (comments, source_file_path, source_code, line_number)

class NewVariable(AbstractNewVariable):

    def to_column(self, tax_benefit_system):

        formula_class = SimpleFormula # To change for DatedFormulas
        entity_class = self.attributes.pop('entity_class', None)

        # Reform variable that replaces the existing reference one
        reference_column = None
        reference = self.attributes.pop('reference', None)
        if reference:
            reference_column = tax_benefit_system.get_column(reference)
            formula_class = reference_column.formula_class
            entity_class = reference_column.entity_class

        (comments, source_file_path, source_code, line_number) = self.introspect()

        if entity_class is None: raise Exception('Variable {} must have an entity_class'.format(self.name))

        return new_filled_column(
            name = self.name,
            entity_class = entity_class,
            formula_class = formula_class,
            reference_column = reference_column,
            comments = comments,
            line_number = line_number,
            source_code = source_code,
            source_file_path = source_file_path,
            base_function = self.attributes.pop('base_function', UnboundLocalError),
            calculate_output = self.attributes.pop('calculate_output', UnboundLocalError),
            cerfa_field = self.attributes.pop('cerfa_field', UnboundLocalError),
            column = self.attributes.pop('column', UnboundLocalError),
            doc = self.attributes.pop('doc', UnboundLocalError),
            is_permanent = self.attributes.pop('is_permanent', UnboundLocalError),
            label = self.attributes.pop('label', UnboundLocalError),
            law_reference = self.attributes.pop('law_reference', UnboundLocalError),
            module = self.attributes.pop('module', UnboundLocalError),
            set_input = self.attributes.pop('set_input', UnboundLocalError),
            start_date = self.attributes.pop('start_date', UnboundLocalError),
            stop_date = self.attributes.pop('stop_date', UnboundLocalError),
            url = self.attributes.pop('url', UnboundLocalError),
            **self.attributes
            )


class NewEntityToPersonColumn(AbstractNewVariable):
    def to_column(self, tax_benefit_system):

        formula_class = EntityToPerson # To change for PersonToEntity

        # Extract attributes.

        cerfa_field = self.attributes.pop('cerfa_field', None)
        if cerfa_field is not None:
            assert isinstance(cerfa_field, basestring), cerfa_field
            cerfa_field = unicode(cerfa_field)

        doc = self.attributes.pop('doc', None)

        entity_class = self.attributes.pop('entity_class')

        label = self.attributes.pop('label', None)
        label = self.name if label is None else unicode(label)

        law_reference = self.attributes.pop('law_reference', None)
        if law_reference is not None:
            assert isinstance(law_reference, (basestring, list))

        url = self.attributes.pop('url', None)
        if url is not None:
            url = unicode(url)

        reference_variable_name = self.attributes.pop('variable')
        reference_column = tax_benefit_system.get_column(reference_variable_name)

        assert reference_column is not None

        # Build formula class and column from extracted attributes.

        formula_class_attributes = dict(
            __module__ = self.attributes.pop('module'),
            )
        if doc is not None:
            formula_class_attributes['__doc__'] = doc

        (comments, source_file_path, source_code, line_number) = self.introspect()

        if comments is not None:
            if isinstance(comments, str):
                comments = comments.decode('utf-8')
            formula_class_attributes['comments'] = comments
        if source_file_path is not None:
            formula_class_attributes['source_file_path'] = source_file_path
        if source_code is not None:
            formula_class_attributes['source_code'] = source_code
        if line_number is not None:
            formula_class_attributes['line_number'] = line_number

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

        if issubclass(formula_class, EntityToPerson):
            assert entity_class.is_persons_entity
            column = reference_column.empty_clone()
        else:
            assert issubclass(formula_class, PersonToEntity)

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
        assert not self.attributes, 'Unexpected attributes in definition of filled column {}: {}'.format(self.name,
            ', '.join(attributes.iterkeys()))

        formula_class = type(self.name.encode('utf-8'), (formula_class,), formula_class_attributes)

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

