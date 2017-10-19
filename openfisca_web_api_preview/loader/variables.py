# -*- coding: utf-8 -*-

import datetime
import inspect
import textwrap


def get_next_day(date):
    parsed_date = date
    next_day = parsed_date + datetime.timedelta(days = 1)
    return next_day.isoformat().split('T')[0]


def get_default_value(variable):
    default_value = variable.default
    if isinstance(default_value, datetime.date):
        return default_value.isoformat()
    if variable.value_type == 'Enum':
        return variable.possible_values._vars[default_value]
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


def build_formula(formula, country_package_metadata, source_file_path, tax_benefit_system):
    source_code, start_line_number = inspect.getsourcelines(formula.formula)
    if source_code[0].lstrip(' ').startswith('@'):  # remove decorator
        source_code = source_code[1:]
        start_line_number = start_line_number + 1
    source_code = textwrap.dedent(''.join(source_code))
    return {
        'source': build_source_url(
            country_package_metadata,
            source_file_path,
            start_line_number,
            source_code
            ),
        'content': source_code,
        }


def build_formulas(dated_formulas, country_package_metadata, source_file_path, tax_benefit_system):
    def get_start_or_default(dated_formula):
        return dated_formula['start_instant'].date.isoformat() if dated_formula['start_instant'] else '0001-01-01'

    return {
        get_start_or_default(dated_formula): build_formula(dated_formula['formula_class'], country_package_metadata, source_file_path, tax_benefit_system)
        for dated_formula in dated_formulas
        }


def build_variable(variable, country_package_metadata, tax_benefit_system):
    comments, source_file_path, source_code, start_line_number = variable.get_introspection_data(tax_benefit_system)
    result = {
        'id': variable.name,
        'description': variable.label,
        'valueType': 'String' if variable.json_type == 'Enumeration' else variable.json_type,
        'defaultValue': get_default_value(variable),
        'definitionPeriod': variable.definition_period.upper(),
        'entity': variable.entity.key,
        'source': build_source_url(
            country_package_metadata,
            source_file_path,
            start_line_number,
            source_code
            ),
        }

    if variable.reference:
        result['references'] = variable.reference
    if hasattr(variable.formula, 'function') and variable.formula.function:
        result['formulas'] = {
            '0001-01-01': build_formula(variable.formula, country_package_metadata, source_file_path, tax_benefit_system)
            }
    if hasattr(variable.formula, 'dated_formulas_class'):
        result['formulas'] = build_formulas(variable.formula.dated_formulas_class, country_package_metadata, source_file_path, tax_benefit_system)

        if variable.end:
            result['formulas'][get_next_day(variable.end)] = None

    if variable.value_type == 'Enum':
        result['possibleValues'] = variable.possible_values.list

    return result


def build_variables(tax_benefit_system, country_package_metadata):
    return {
        name: build_variable(variable, country_package_metadata, tax_benefit_system)
        for name, variable in tax_benefit_system.variables.iteritems()
        }
