# -*- coding: utf-8 -*-

import datetime
import inspect
import textwrap

from openfisca_core.columns import EnumCol


def get_next_day(date):
    parsed_date = date
    next_day = parsed_date + datetime.timedelta(days = 1)
    return next_day.isoformat().split('T')[0]


def get_default_value(variable):
    default_value = variable.default
    if isinstance(default_value, datetime.date):
        return default_value.isoformat()
    if isinstance(variable, EnumCol):
        return variable.enum._vars[default_value]
    return default_value


def build_source_url(country_package_metadata, source_file_path, start_line_number, source_code):
    nb_lines = source_code.count('\n')
    return '{}/blob/{}{}#L{}-L{}'.format(
        country_package_metadata['repository_url'],
        country_package_metadata['version'],
        source_file_path,
        start_line_number,
        start_line_number + nb_lines - 1,
        ).encode('utf-8')


def build_formula(formula, country_package_metadata):
    source_code, start_line_number = inspect.getsourcelines(formula.formula)
    if source_code[0].lstrip(' ').startswith('@'):  # remove decorator
        source_code = source_code[1:]
        start_line_number = start_line_number + 1
    source_code = textwrap.dedent(''.join(source_code))

    return {
        'source': build_source_url(
            country_package_metadata,
            formula.source_file_path,
            start_line_number,
            source_code
            ),
        'content': source_code,
        }


def get_variable_type(variable):
    column_type = variable.__class__.__name__
    return 'String' if column_type == 'EnumCol' else column_type.replace('Col', '')


def build_formulas(dated_formulas, country_package_metadata):
    def get_start_or_default(dated_formula):
        return dated_formula['start_instant'].date.isoformat() if dated_formula['start_instant'] else '0001-01-01'

    return {
        get_start_or_default(dated_formula): build_formula(dated_formula['formula_class'], country_package_metadata)
        for dated_formula in dated_formulas
        }


def build_variable(variable, country_package_metadata):
    result = {
        'id': variable.name,
        'description': variable.label,
        'valueType': get_variable_type(variable),
        'defaultValue': get_default_value(variable),
        'definitionPeriod': variable.definition_period.upper(),
        'entity': variable.entity.key,
        'source': build_source_url(
            country_package_metadata,
            variable.formula_class.source_file_path,
            variable.formula_class.start_line_number,
            variable.formula_class.source_code
            ),
        }

    if variable.reference:
        result['references'] = variable.reference
    if hasattr(variable.formula_class, 'function') and variable.formula_class.function:
        result['formulas'] = {
            '0001-01-01': build_formula(variable.formula_class, country_package_metadata)
            }
    if hasattr(variable.formula_class, 'dated_formulas_class'):
        result['formulas'] = build_formulas(variable.formula_class.dated_formulas_class, country_package_metadata)

        if variable.end:
            result['formulas'][get_next_day(variable.end)] = None

    if isinstance(variable, EnumCol):
        result['possibleValues'] = variable.enum.list

    return result


def build_variables(tax_benefit_system, country_package_metadata):
    return {
        name: build_variable(variable, country_package_metadata)
        for name, variable in tax_benefit_system.column_by_name.iteritems()
        }
