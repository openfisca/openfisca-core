# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
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


def build_api_scale(scale):
    # preprocess brackets
    brackets = [{
        'thresholds': build_api_values_history(bracket.threshold),
        'rates': build_api_values_history(bracket.rate),
        } for bracket in scale.brackets]

    dates = set(sum(
        [list(bracket['thresholds'].keys()) + list(bracket['rates'].keys()) for bracket in brackets],
        []))  # flatten the dates and remove duplicates

    # We iterate on all dates as we need to build the whole scale for each of them
    api_scale = {}
    for date in dates:
        for bracket in brackets:
            threshold_value = get_value(date, bracket['thresholds'])
            if threshold_value is not None:
                rate_value = get_value(date, bracket['rates'])
                api_scale[date] = api_scale.get(date) or {}
                api_scale[date][threshold_value] = rate_value

    # Handle stopped parameters: a parameter is stopped if its first bracket is stopped
    latest_date_first_threshold = max(brackets[0]['thresholds'].keys())
    latest_value_first_threshold = brackets[0]['thresholds'][latest_date_first_threshold]
    if latest_value_first_threshold is None:
        api_scale[latest_date_first_threshold] = None

    return api_scale


def walk_node(node, parameters, path_fragments):
    children = node.children

    for child_name, child in children.items():
        api_parameter = {
            'description': getattr(child, "description", None),
            'id': '.'.join(path_fragments + [child_name]),
            }
        if child.reference:
            api_parameter['references'] = child.reference

        if isinstance(child, Parameter):
            api_parameter['values'] = build_api_values_history(child)
            if child.unit:
                api_parameter['unit'] = child.unit
        elif isinstance(child, Scale):
            if child.unit:
                api_parameter['unit'] = child.unit
            api_parameter['brackets'] = build_api_scale(child)
        elif isinstance(child, ParameterNode):
            api_parameter['children'] = {
                grandchild_name: {
                    'description': grandchild.description,
                    'id': '.'.join(path_fragments + [child_name, grandchild_name])
                    }
                for grandchild_name, grandchild in child.children.items()
                }
            walk_node(child, parameters, path_fragments + [child_name])
        parameters.append(api_parameter)


def build_parameters(tax_benefit_system):
    original_parameters = tax_benefit_system.parameters
    api_parameters = []
    walk_node(
        original_parameters,
        parameters = api_parameters,
        path_fragments = [],
        )

    return {parameter['id']: parameter for parameter in api_parameters}
