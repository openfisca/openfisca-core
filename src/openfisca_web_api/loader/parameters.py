# -*- coding: utf-8 -*-

from openfisca_core.parameters import Parameter, ParameterNode, Scale


def build_api_values_history(values_history):
    api_values_history = {}
    for value_at_instant in values_history.values_list:
        api_values_history[value_at_instant.instant_str] = value_at_instant.value

    return api_values_history


def get_value(date, values):
    candidates = sorted([
        (start_date, value)
        for start_date, value in values.items()
        if start_date <= date  # dates are lexicographically ordered and can be sorted
        ], reverse = True)

    if candidates:
        return candidates[0][1]
    else:
        return None


def build_api_scale(scale, value_key_name):
    # preprocess brackets for a scale with 'rates' or 'amounts'
    brackets = [{
        'thresholds': build_api_values_history(bracket.threshold),
        'values': build_api_values_history(getattr(bracket, value_key_name))
        } for bracket in scale.brackets]

    dates = set(sum(
        [list(bracket['thresholds'].keys())
        + list(bracket['values'].keys()) for bracket in brackets],
        []))  # flatten the dates and remove duplicates

    # We iterate on all dates as we need to build the whole scale for each of them
    api_scale = {}
    for date in dates:
        for bracket in brackets:
            threshold_value = get_value(date, bracket['thresholds'])
            if threshold_value is not None:
                rate_or_amount_value = get_value(date, bracket['values'])
                api_scale[date] = api_scale.get(date) or {}
                api_scale[date][threshold_value] = rate_or_amount_value

    # Handle stopped parameters: a parameter is stopped if its first bracket is stopped
    latest_date_first_threshold = max(brackets[0]['thresholds'].keys())
    latest_value_first_threshold = brackets[0]['thresholds'][latest_date_first_threshold]

    if latest_value_first_threshold is None:
        api_scale[latest_date_first_threshold] = None

    return api_scale


def build_source_url(absolute_file_path, country_package_metadata):
    relative_path = absolute_file_path.replace(country_package_metadata['location'], '')
    return '{}/blob/{}{}'.format(
        country_package_metadata['repository_url'],
        country_package_metadata['version'],
        relative_path
        )


def build_api_parameter(parameter, country_package_metadata):
    api_parameter = {
        'description': getattr(parameter, "description", None),
        'id': parameter.name,
        'metadata': parameter.metadata
        }
    if parameter.file_path:
        api_parameter['source'] = build_source_url(parameter.file_path, country_package_metadata)
    if isinstance(parameter, Parameter):
        if parameter.documentation:
            api_parameter['documentation'] = parameter.documentation.strip()
        api_parameter['values'] = build_api_values_history(parameter)
    elif isinstance(parameter, Scale):
        if 'rate' in parameter.brackets[0].children:
            api_parameter['brackets'] = build_api_scale(parameter, 'rate')
        elif 'amount' in parameter.brackets[0].children:
            api_parameter['brackets'] = build_api_scale(parameter, 'amount')
    elif isinstance(parameter, ParameterNode):
        if parameter.documentation:
            api_parameter['documentation'] = parameter.documentation.strip()
        api_parameter['subparams'] = {
            child_name: {
                'description': child.description,
                }
            for child_name, child in parameter.children.items()
            }
    return api_parameter


def build_parameters(tax_benefit_system, country_package_metadata):
    return {
        parameter.name.replace('.', '/'): build_api_parameter(parameter, country_package_metadata)
        for parameter in tax_benefit_system.parameters.get_descendants()
        }
