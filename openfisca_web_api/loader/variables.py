import datetime
import inspect
import textwrap

from openfisca_core.indexed_enums import Enum
from openfisca_core.variables import VALUE_TYPES


def get_next_day(date):
    parsed_date = date
    next_day = parsed_date + datetime.timedelta(days=1)
    return next_day.isoformat().split("T")[0]


def get_default_value(variable):
    default_value = variable.default_value
    if isinstance(default_value, datetime.date):
        return default_value.isoformat()

    if isinstance(default_value, Enum):
        return default_value.name

    return default_value


def build_source_url(
    country_package_metadata,
    source_file_path,
    start_line_number,
    source_code,
):
    nb_lines = source_code.count("\n")
    return "{}/blob/{}{}#L{}-L{}".format(
        country_package_metadata["repository_url"],
        country_package_metadata["version"],
        source_file_path,
        start_line_number,
        start_line_number + nb_lines - 1,
    )


def build_formula(formula, country_package_metadata, source_file_path):
    source_code, start_line_number = inspect.getsourcelines(formula)

    source_code = textwrap.dedent("".join(source_code))

    api_formula = {
        "source": build_source_url(
            country_package_metadata,
            source_file_path,
            start_line_number,
            source_code,
        ),
        "content": source_code,
    }

    if formula.__doc__:
        api_formula["documentation"] = textwrap.dedent(formula.__doc__)

    return api_formula


def build_formulas(formulas, country_package_metadata, source_file_path):
    return {
        start_date: build_formula(formula, country_package_metadata, source_file_path)
        for start_date, formula in formulas.items()
    }


def build_variable(variable, country_package_metadata):
    (
        source_file_path,
        source_code,
        start_line_number,
    ) = variable.get_introspection_data()
    result = {
        "id": variable.name,
        "description": variable.label,
        "valueType": VALUE_TYPES[variable.value_type]["formatted_value_type"],
        "defaultValue": get_default_value(variable),
        "definitionPeriod": variable.definition_period.upper(),
        "entity": variable.entity.key,
    }

    if source_code:
        result["source"] = build_source_url(
            country_package_metadata,
            source_file_path,
            start_line_number,
            source_code,
        )

    if variable.documentation:
        result["documentation"] = variable.documentation.strip()

    if variable.reference:
        result["references"] = variable.reference

    if len(variable.formulas) > 0:
        result["formulas"] = build_formulas(
            variable.formulas,
            country_package_metadata,
            source_file_path,
        )

        if variable.end:
            result["formulas"][get_next_day(variable.end)] = None

    if variable.value_type == Enum:
        result["possibleValues"] = {
            item.name: item.value for item in list(variable.possible_values)
        }

    return result


def build_variables(tax_benefit_system, country_package_metadata):
    return {
        name: build_variable(variable, country_package_metadata)
        for name, variable in tax_benefit_system.variables.items()
    }
