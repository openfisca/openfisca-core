# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
from openfisca_core.parameters import Parameter, ParameterNode, Scale
from openfisca_core.taxscales import AmountTaxScale

import logging


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


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

    # try:
    # brackets = [{
    #     'thresholds': build_api_values_history(bracket.threshold),
    #     'rates': build_api_values_history(bracket.rate) if 'rate' in bracket.children else None,
    #     'amounts': build_api_values_history(bracket.amount) if 'amount' in bracket.children else None,
    # } for bracket in scale.brackets]
    # log.debug("---")
    # log.debug(locals())
    # log.debug("---")

    brackets = []
    for bracket in scale.brackets:
        api_toto_bracket = { 'thresholds': build_api_values_history(bracket.threshold) }
        
        if 'rate' in bracket.children:
            api_toto_bracket['rates'] = build_api_values_history(bracket.rate) 
        elif 'amount' in bracket.children:
            api_toto_bracket['amounts'] = build_api_values_history(bracket.amount)
        
        brackets.append(api_toto_bracket) 

    log.debug("---")
    log.debug(locals())
    log.debug("---")

    # except AttributeError:
        #log.debug(locals())



    dates = set(sum(
        [list(bracket['thresholds'].keys()) 
        + list(bracket['rates'].keys() if 'rates' in bracket else [])
        + list(bracket['amounts'].keys() if 'amounts' in bracket else []) for bracket in brackets],
        []))  # flatten the dates and remove duplicates

    # We iterate on all dates as we need to build the whole scale for each of them
    api_scale = {}
    for date in dates:
        for bracket in brackets:
            rates_or_amounts = {}
            if 'rates' in bracket:
                rates_or_amounts = bracket['rates']
            elif 'amounts' in bracket:
                rates_or_amounts = bracket['amounts']

            threshold_value = get_value(date, bracket['thresholds'])
            if threshold_value is not None:
                rate_or_amount_value = get_value(date, rates_or_amounts)
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


def walk_node(node, parameters, path_fragments, country_package_metadata):
    children = node.children

    for child_name, child in children.items():
        api_parameter = {
            'description': getattr(child, "description", None),
            'id': '.'.join(path_fragments + [child_name]),
            'metadata': child.metadata
            }
        if child.file_path:
            api_parameter['source'] = build_source_url(child.file_path, country_package_metadata)
        if isinstance(child, Parameter):
            if child.documentation:
                api_parameter['documentation'] = child.documentation.strip()
            api_parameter['values'] = build_api_values_history(child)
        elif isinstance(child, Scale):
            api_parameter['brackets'] = build_api_scale(child)
        elif isinstance(child, ParameterNode):
            if child.documentation:
                api_parameter['documentation'] = child.documentation.strip()
            api_parameter['subparams'] = {
                grandchild_name: {
                    'description': grandchild.description,
                    }
                for grandchild_name, grandchild in child.children.items()
                }
            walk_node(child, parameters, path_fragments + [child_name], country_package_metadata)
        parameters.append(api_parameter)


def build_parameters(tax_benefit_system, country_package_metadata):
    original_parameters = tax_benefit_system.parameters
    api_parameters = []
    walk_node(
        original_parameters,
        parameters = api_parameters,
        path_fragments = [],
        country_package_metadata = country_package_metadata,
        )

    return {parameter['id'].replace('.', '/'): parameter for parameter in api_parameters}
