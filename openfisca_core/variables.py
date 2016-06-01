import inspect, textwrap
from openfisca_core.formulas import SimpleFormula, new_filled_column

class AbstractNewVariable():
    def __init__(self, name, attributes, variable_class):
        self.name = name
        self.attributes = { attr_name.strip('_'): attr_value for (attr_name, attr_value) in attributes.iteritems() }
        self.variable_class = variable_class

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

