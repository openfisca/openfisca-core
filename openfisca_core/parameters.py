# Parse YAML parameters and filter them based on the given period & variable values

from openfisca_core import taxscales, legislations
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
                    if parentNode is None:
                        node.update(options['transform'](value))
                    else:
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
def get(parameters, collection, variable, instant, bareme_parameters=None,**vector_variables):
    # Get the requested parameter from the requested collection
    # TODO : parse the relevant YAML collection here on the fly, cache it in tax_benefit_system
    parameter = next((x for x in parameters[collection] if x['variable'] == variable), None)
    if parameter is None:
        message = "Parameter \"{0}\" not found in collection \"{1}\"".format(variable, collection)
        raise legislations.ParameterNotFound(instant=instant, name=variable)  # TODO don't raise general Exception !

    # select and set the right value for this instant
    transform_dict_key(
        parameter,
        dict(key_to_find='VALUES', new_key='VALUE',
             transform=lambda values: choose_value(values, instant)),
    )

    # filter VAR cases using variables
    # remember : we're working on vector variables
    resolved_parameter = resolve_var_cases(vector_variables, parameter)

    # Compute scales if it is a BAREME
    parameter_with_scales = compute_scales(resolved_parameter, bareme_parameters)

    return parameter_with_scales['VALUE']


def get_parameter_value(node, attribute, default=None):
    value = node.get(attribute)
    if value:
        return value['VALUE']
    else:
        assert default is not None
        return default


def to_vector(element, vector_size):
    if isinstance(element, (int, float)):
        vector = np.empty(vector_size)
        vector.fill(element)
        return vector
    return element


def compute_scales(parameter, bareme_parameters):
    bareme = parameter.get('BAREME')
    if not bareme:
        return parameter
    else:
        assert bareme_parameters is not None
        base = bareme_parameters.get('base')
        factor = bareme_parameters.get('factor')
        for element in [base, factor]:
            assert element is not None

        nb_entities = len(base)
        thresholds = list()
        rates = list()
        # Only the case of the MarginalRateTaxScale is supported in YAML parameters
        # Construct the tax scale
        tax_scale = taxscales.MarginalRateTaxScale(name=parameter.get('variable'))
        for tranche in bareme:
            assiette = get_parameter_value(tranche, 'ASSIETTE', 1)
            taux = get_parameter_value(tranche, 'TAUX')
            seuil = get_parameter_value(tranche, 'SEUIL')
            # transform scalar to vector
            rates.append(to_vector(taux * assiette, nb_entities))
            thresholds.append(to_vector(seuil, nb_entities))
        parameter['tax_scale'] = tax_scale
    return {'VALUE': parameter['tax_scale'].calc(base, factor, thresholds=thresholds, rates=rates)}


def resolve_var_cases(vector_variables, parameter):
    parameter_copy = copy.deepcopy(parameter)
    transform_dict_key(
        parameter_copy,
        dict(key_to_find='VAR', replace_parent=True,
             transform=lambda cases: choose_conditional_case(cases, vector_variables)),
    )

    return parameter_copy


def choose_conditional_case(cases, variables):
    # The first value whose case is evaluated to true is selected (for each entity of our entity vector)
    case_conditions = np.array([resolve_condition(case['condition'], variables) for case in cases])
    case_values = [case['VALUE'] for case in cases]
    return {
        'VALUE': np.select(case_conditions, case_values)
    }


def resolve_condition(condition_string, variables):
    return eval(condition_string, variables)
