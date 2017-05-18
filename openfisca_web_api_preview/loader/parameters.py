# -*- coding: utf-8 -*-


def build_values(values):
    result = {}
    for value_object in values:
        result[value_object['start']] = value_object.get('value')

    return result


def get_value(date, values):
    candidates = sorted([
        (start_date, value)
        for start_date, value in values.iteritems()
        if start_date <= date  # dates are lexicographically ordered and can be sorted
        ], reverse = True)

    if candidates:
        return candidates[0][1]
    else:
        return None


def build_brackets(brackets):
    result = {}
    # preprocess brackets
    brackets = [{
        'thresholds': build_values(bracket['threshold']),
        'rates': build_values(bracket['rate']),
        } for bracket in brackets]

    dates = set(sum(
        [bracket['thresholds'].keys() + bracket['rates'].keys() for bracket in brackets],
        []))  # flatten the dates and remove duplicates

    # We iterate on all dates as we need to build the whole scale for each of them
    for date in dates:
        for bracket in brackets:
            threshold_value = get_value(date, bracket['thresholds'])
            if threshold_value is not None:
                rate_value = get_value(date, bracket['rates'])
                result[date] = result.get(date) or {}
                result[date][threshold_value] = rate_value

    # Handle stopped parameters: a parameter is stopped if its first bracket is stopped
    latest_date_first_threshold = max(brackets[0]['thresholds'].keys())
    latest_value_first_threshold = brackets[0]['thresholds'][latest_date_first_threshold]
    if latest_value_first_threshold is None:
        result[latest_date_first_threshold] = None

    return result


def build_parameter(parameter_json, parameter_path):
    result = {
        'description': parameter_json.get('description'),
        'id': parameter_path,
        }
    if parameter_json.get('values'):
        result['values'] = build_values(parameter_json['values'])
    elif parameter_json.get('brackets'):
        result['brackets'] = build_brackets(parameter_json['brackets'])
    return result


def walk_legislation_json(node_json, parameters_json, path_fragments):
    children_json = node_json.get('children') or None
    if children_json is None:
        parameter = build_parameter(node_json, u'.'.join(path_fragments))
        parameters_json.append(parameter)
    else:
        for child_name, child_json in children_json.iteritems():
            walk_legislation_json(
                child_json,
                parameters_json = parameters_json,
                path_fragments = path_fragments + [child_name],
                )


def build_parameters(tax_benefit_system):
    legislation_json = tax_benefit_system.get_legislation()
    parameters_json = []
    walk_legislation_json(
        legislation_json,
        parameters_json = parameters_json,
        path_fragments = [],
        )

    return {parameter['id']: parameter for parameter in parameters_json}
