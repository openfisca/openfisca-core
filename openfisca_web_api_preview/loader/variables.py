# -*- coding: utf-8 -*-

import datetime
import inspect
import textwrap

from openfisca_core.indexed_enums import Enum
from openfisca_core.commons import to_unicode


def get_next_day(date):
    parsed_date = date
    next_day = parsed_date + datetime.timedelta(days = 1)
    return next_day.isoformat().split('T')[0]


def get_default_value(variable):
    default_value = variable.default_value
    if isinstance(default_value, datetime.date):
        return default_value.isoformat()

    if isinstance(default_value, Enum):
        return default_value.name

    return default_value


def build_source_url(country_package_metadata, source_file_path, start_line_number, source_code):
    nb_lines = source_code.count('\n')
    return u'{}/blob/{}{}#L{}-L{}'.format(
        country_package_metadata['repository_url'],
        country_package_metadata['version'],
        source_file_path,
        start_line_number,
        start_line_number + nb_lines - 1,
        )


def build_formula(formula, country_package_metadata, source_file_path, tax_benefit_system):
    source_code, start_line_number = inspect.getsourcelines(formula)
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
        'content': to_unicode(source_code),
        }


def build_formulas(formulas, country_package_metadata, source_file_path, tax_benefit_system):
    return {
        start_date: build_formula(formula, country_package_metadata, source_file_path, tax_benefit_system)
        for start_date, formula in formulas.items()
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

    if len(variable.formulas) > 0:
        result['formulas'] = build_formulas(variable.formulas, country_package_metadata, source_file_path, tax_benefit_system)

        if variable.end:
            result['formulas'][get_next_day(variable.end)] = None

    if variable.value_type == Enum:
        result['possibleValues'] = {item.name: item.value for item in list(variable.possible_values)}

    return result


def build_variables(tax_benefit_system, country_package_metadata):
    return {
        name: build_variable(variable, country_package_metadata, tax_benefit_system)
        for name, variable in tax_benefit_system.variables.items()
        }
