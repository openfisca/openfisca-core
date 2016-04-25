from . import conv
import copy
import numpy as np


# Helpers to access, set and transform dict values


def get_from_dict(data_dict, map_list):
    return reduce(lambda d, k: d[k], map_list, data_dict)


def set_in_dict(data_dict, map_list, value):
    get_from_dict(data_dict, map_list[:-1])[map_list[-1]] = value


def transform_dict_key(node, options, parentNode=None, parentKey=None):
    if isinstance(node, list):
        [transform_dict_key(element, options) for element in node]
    if isinstance(node, dict):
        for key, value in node.items():
            if key == options['key_to_find']:
                if options.get('replace_parent'):
                    parentNode[parentKey] = options['transform'](value)
                elif options.get('new_key'):
                    node[options['new_key']] = options['transform'](value)
                    del node[options['key_to_find']]
            else:
                transform_dict_key(value, options, node, key)


def convert_value_date(date):
    return conv.date_to_iso8601_str(date)[0]


def choose_value(values, instant):
    for value in values:
        beginning = convert_value_date(value['deb'])
        end = convert_value_date(value['fin']) if value.get('fin') else None

        if end is None and value.get('fuzzy') is None:
            raise Exception(
                'Please set a "fin" date or set "fuzzy" to true in your parameters')  # TODO don't raise general Exception !

        if beginning <= instant and (end is None or instant <= end):
            return value['valeur']

    return None


##################
#  MAIN FUNCTION
##################
def get_parameter(parameters, collection, variable, instant, **vector_variables):
    # Get the requested parameter from the requested collection
    parameter = next((x for x in parameters[collection] if x['variable'] == variable), None)
    if parameter is None:
        message = "Parameter \"{0}\" not found in collection \"{1}\"".format(variable, collection)
        raise Exception(message)  # TODO don't raise general Exception !

    # select and set the right value for this instant
    transform_dict_key(
        parameter,
        dict(key_to_find='VALUES', new_key='VALUE',
             transform=lambda values: choose_value(values, instant)),
    )

    # filter VAR cases using variables
    # remember : we're working on vector variables
    # -> there will be as many parameter objects as variable dimensions
    # TODO :-D

    return resolve_var_cases(vector_variables, parameter)
    #TODO generate scales and other objects



def resolve_var_cases(vector_variables, parameter):
    parameter_copy = copy.deepcopy(parameter)
    transform_dict_key(
        parameter_copy,
        dict(key_to_find='VAR', replace_parent=True,
             transform=lambda cases: choose_conditional_case(cases, vector_variables)),
    )

    return parameter_copy


def choose_conditional_case(cases, variables):
    return np.sum(
        (resolve_condition(case['condition'], variables) * case['VALUE']
            for case in cases))


def resolve_condition(condition_string, variables):
    return eval(condition_string, variables)
