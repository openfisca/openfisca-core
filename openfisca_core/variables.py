# -*- coding: utf-8 -*-


import inspect
import textwrap
import datetime

import columns
import entities
from periods import MONTH, YEAR, ETERNITY



class Variable(object):

    @classmethod
    def build_variable(variable_class):
        name = unicode(variable_class.__name__)
        attributes = dict(variable_class.__dict__)

    def __init__(self):
        self.name = self.__class__.__name__
        attributes = dict(self.__class__.__dict__)
        self.column = self.set_column(attributes.pop('column', None))
        self.default = self.column.default
        self.entity = self.set_entity(attributes.pop('entity', None))
        self.definition_period = self.set_definition_period(attributes.pop('definition_period', None))
        self.label = self.set_label(attributes.pop('label', None))
        self.end = self.set_end(attributes.pop('end', None))
        self.reference = self.set_reference(attributes.pop('reference', None))
        self.cerfa_field = self.set_cerfa_field(attributes.pop('cerfa_field', None))
        self.calculate_output = attributes.pop('calculate_output', None)


        # self.variable_class = variable_class


    def set_column(self, column):
        if not column:
            raise ValueError("Missing attribute 'column' in definition of variable {}".format(self.name).encode('utf-8'))
        if issubclass(column, columns.Column):
            return column()
        if isinstance(column, column.Column):
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


    # def to_column(self, tax_benefit_system):
        # entity = self.attributes.pop('entity', None)

        # For reform variable that replaces an existing baseline one
        # baseline_variable = self.attributes.pop('baseline_variable', None)
        # if baseline_variable:
        #     if not entity:
        #         entity = baseline_variable.entity

        # comments, source_file_path, source_code, start_line_number = self.get_introspection_data(tax_benefit_system)

        # if entity is None:
        #     raise Exception('Variable {} must have an entity'.format(self.name))



        # return new_filled_column(
        #     name = self.name,
        #     entity = entity,
        #     end = end_date,
        #     baseline_variable = baseline_variable,
        #     comments = comments,
        #     start_line_number = start_line_number,
        #     source_code = source_code,
        #     source_file_path = source_file_path,
        #     reference = reference,
        #     **self.attributes
        #     )

    def new_filled_column(
            __doc__ = None,
            __module__ = None,
            base_function = UnboundLocalError,
            calculate_output = UnboundLocalError,
            cerfa_field = UnboundLocalError,
            column = UnboundLocalError,
            comments = UnboundLocalError,
            default = UnboundLocalError,
            definition_period = UnboundLocalError,
            entity = UnboundLocalError,
            is_neutralized = False,
            label = UnboundLocalError,
            name = None,
            baseline_variable = None,
            set_input = UnboundLocalError,
            source_code = UnboundLocalError,
            source_file_path = UnboundLocalError,
            start_line_number = UnboundLocalError,
            end = UnboundLocalError,
            reference = UnboundLocalError,
            **specific_attributes
            ):

        # Validate arguments.

        if baseline_variable is not None:
            assert isinstance(baseline_variable, columns.Column)
            if name is None:
                name = baseline_variable.name

        # assert isinstance(name, unicode)

        # if calculate_output is UnboundLocalError:
        #     calculate_output = None if baseline_variable is None else baseline_variable.formula_class.calculate_output.im_func

        # if cerfa_field is UnboundLocalError:
        #     cerfa_field = None if baseline_variable is None else baseline_variable.cerfa_field
        # elif cerfa_field is not None:
        #     assert isinstance(cerfa_field, (basestring, dict)), cerfa_field

        # assert column is not None, """Missing attribute "column" in definition of filled column {}""".format(name)
        # if column is UnboundLocalError:
        #     assert baseline_variable is not None, """Missing attribute "column" in definition of filled column {}""".format(
        #         name)
        #     column = baseline_variable.empty_clone()
        # elif not isinstance(column, columns.Column):
        #     column = column()
        #     assert isinstance(column, columns.Column)

        # if comments is UnboundLocalError:
        #     comments = None if baseline_variable is None else baseline_variable.formula_class.comments
        # elif isinstance(comments, str):
        #     comments = comments.decode('utf-8')

        # if default is UnboundLocalError:
        #     default = column.default if baseline_variable is None else baseline_variable.default

        # assert entity is not None, """Missing attribute "entity" in definition of filled column {}""".format(
            # name)
        # if entity is UnboundLocalError:
        #     assert base:line_variable is not None, \
        #         """Missing attribute "entity" in definition of filled column {}""".format(name)
        #     entity = baseline_variable.entity

        # if definition_period is UnboundLocalError:
        #     if baseline_variable:
        #         definition_period = baseline_variable.definition_period
            # else:
            #     raise ValueError(u'definition_period missing in {}'.format(name).encode('utf-8'))
        # if definition_period not in (MONTH, YEAR, ETERNITY):
        #     raise ValueError(u'Incorrect definition_period ({}) in {}'.format(definition_period, name).encode('utf-8'))

        # if label is UnboundLocalError:
        #     label = None if baseline_variable is None else baseline_variable.label
        # else:
        #     label = None if label is None else unicode(label)

        # if start_line_number is UnboundLocalError:
        #     start_line_number = None if baseline_variable is None else baseline_variable.formula_class.start_line_number
        # elif isinstance(start_line_number, str):
        #     start_line_number = start_line_number.decode('utf-8')

        # if set_input is UnboundLocalError:
        #     set_input = None if baseline_variable is None else baseline_variable.formula_class.set_input.im_func

        # if source_code is UnboundLocalError:
        #     source_code = None if baseline_variable is None else baseline_variable.formula_class.source_code
        # elif isinstance(source_code, str):
        #     source_code = source_code.decode('utf-8')

        # if source_file_path is UnboundLocalError:
        #     source_file_path = None if baseline_variable is None else baseline_variable.formula_class.source_file_path
        # elif isinstance(source_file_path, str):
        #     source_file_path = source_file_path.decode('utf-8')

        # if end is UnboundLocalError:
        #     end = None if baseline_variable is None else baseline_variable.end

        # if reference is UnboundLocalError:
        #     reference = None if baseline_variable is None else baseline_variable.reference
        # elif reference is not None:
        #     if isinstance(reference, list):
        #         reference = map(unicode, reference)
        #     else:
        #         reference = [unicode(reference)]

        # Build formula class and column.

        formula_class_attributes = {}
        if __doc__ is not None:
            formula_class_attributes['__doc__'] = __doc__
        if __module__ is not None:
            formula_class_attributes['__module__'] = __module__
        if comments is not None:
            formula_class_attributes['comments'] = comments
        if start_line_number is not None:
            formula_class_attributes['start_line_number'] = start_line_number
        if source_code is not None:
            formula_class_attributes['source_code'] = source_code
        if source_file_path is not None:
            formula_class_attributes['source_file_path'] = source_file_path

        if column.definition_period == ETERNITY:
            assert base_function == UnboundLocalError, 'Unexpected base_function {}'.format(base_function)
            base_function = permanent_default_value
        elif column.is_period_size_independent:
            assert base_function in (missing_value, requested_period_last_value, requested_period_last_or_next_value, UnboundLocalError), \
                'Unexpected base_function {}'.format(base_function)
            if base_function is UnboundLocalError:
                base_function = requested_period_last_value
        elif base_function is UnboundLocalError:
            base_function = requested_period_default_value

        if base_function is UnboundLocalError:
            assert baseline_variable is not None \
                and issubclass(baseline_variable.formula_class, Formula), \
                """Missing attribute "base_function" in definition of filled column {}""".format(name)
            base_function = baseline_variable.formula_class.base_function
        else:
            assert base_function is not None, \
                """Missing attribute "base_function" in definition of filled column {}""".format(name)
        formula_class_attributes['base_function'] = base_function

        if calculate_output is not None:
            formula_class_attributes['calculate_output'] = calculate_output

        if set_input is not None:
            formula_class_attributes['set_input'] = set_input

        dated_formulas_class = []
        for function_name, function in specific_attributes.copy().iteritems():
            # Turn any formula into a dated formula
            formula_start_date = deduce_formula_date_from_name(function_name)
            if not formula_start_date:
                # Current attribute isn't a formula
                continue

            if end is not None:
                assert end >= formula_start_date, \
                    'You declared that "{}" ends on "{}", but you wrote a formula to calculate it from "{}" ({}). The "end" attribute of a variable must be posterior to the start dates of all its formulas.'.format(name, end, formula_start_date, function_name)
            dated_formula_class_attributes = formula_class_attributes.copy()
            dated_formula_class_attributes['formula'] = function
            dated_formula_class = type(name.encode('utf-8'), (Formula,), dated_formula_class_attributes)

            del specific_attributes[function_name]
            dated_formulas_class.append(dict(
                formula_class = dated_formula_class,
                start_instant = periods.instant(formula_start_date),
                ))

        dated_formulas_class.sort(key = lambda dated_formula_class: dated_formula_class['start_instant'])

        # Add dated formulas defined in (optional) baseline variable when they are not overridden by new dated formulas.
        if baseline_variable is not None:
            for baseline_dated_formula_class in baseline_variable.formula_class.dated_formulas_class:
                baseline_dated_formula_class = baseline_dated_formula_class.copy()
                for dated_formula_class in dated_formulas_class:
                    if baseline_dated_formula_class['start_instant'] >= dated_formula_class['start_instant']:
                        break

                else:
                    dated_formulas_class.append(baseline_dated_formula_class)
            dated_formulas_class.sort(key = lambda dated_formula_class: dated_formula_class['start_instant'])

        formula_class_attributes['dated_formulas_class'] = dated_formulas_class

        assert not specific_attributes.get('start_date'), \
            'Deprecated "start_date" attribute in definition of variable "{}".'.format(name)
        assert not specific_attributes, 'Unexpected attributes in definition of variable "{}": {!r}'.format(name,
            ', '.join(sorted(specific_attributes.iterkeys())))

        formula_class = type(name.encode('utf-8'), (Formula,), formula_class_attributes)

        # Fill column attributes.
        if cerfa_field is not None:
            column.cerfa_field = cerfa_field
        if default != column.default:
            column.default = default
        if end is not None:
            column.end = end
        if reference is not None:
            column.reference = reference
        column.entity = entity
        column.formula_class = formula_class
        column.definition_period = definition_period
        column.is_neutralized = is_neutralized
        column.label = label
        column.name = name

        return column
