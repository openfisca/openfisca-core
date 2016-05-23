# Read YAML parameters and filter them based on the given period & variable values

from openfisca_core import taxscales, legislations
from . import conv
import copy
import numpy as np


##################
#  MAIN FUNCTION
##################
def get(parameters, name, instant, dimension=None, base_options=None, **vector_variables):
    # Get the requested parameter from the collections

    # TODO : parse the relevant YAML collection here on the fly,
    # cache it in tax_benefit_system. Collection would need to be declared somewhere
    parameter = None
    for _, collection in parameters.iteritems():
        treasure = next((x for x in collection if x['variable'] == name), None)
        if treasure is not None:
            parameter = treasure
            break

    if parameter is None:
        message = "Parameter \"{0}\" not found".format(name)
        raise legislations.ParameterNotFound(instant=instant, name=name)

    # select and set the right value for this instant
    transform_dict_key(
        parameter,
        dict(key_to_find='VALUES', new_key='VALUE',
             transform=lambda values: choose_value(values, instant)),
    )

    # filter VAR cases using variables
    # remember : we're working on vector variables
    univoque_parameter = resolve_var_cases(vector_variables, parameter)

    # Now apply specific computations if any : BAREME, LIN...
    value = compute_parameter(univoque_parameter, base_options)

    # A vector should be returned here. Explicitely build one of the right dimension
    # in case it wasn't created (e.g. based on base_options.base)
    return np.zeros(dimension) + value if not isinstance(value, np.ndarray) else value


def compute_parameter(parameter, base_options):
    if parameter.get('BAREME'):
        return compute_scales(parameter, base_options)
    if parameter.get('LIN'):
        return compute_linear(parameter, base_options)
    else:
        return parameter['VALUE']


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

        if beginning <= str(instant) and (end is None or str(instant) <= end):
            return value['valeur']

    return None


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


def certify_base_options(base_options):
    assert base_options is not None
    base = base_options.get('base')
    factor = base_options.get('factor')
    for element in [base, factor]:
        assert element is not None
    return base, factor


def compute_linear(parameter, base_options):
    lin = parameter.get('LIN')
    base, factor = certify_base_options(base_options)
    plafond = lin.get('PLAFOND')

    # Construct a taxscale (see def compute_scales)

    thresholds = list()
    rates = list()
    nb_entities = len(base)
    tax_scale = taxscales.MarginalRateTaxScale(name=parameter.get('variable'))

    # With one bracket only...
    rates.append(to_vector(lin['VALUE'], nb_entities))
    thresholds.append(to_vector(0, nb_entities))

    # ... or two if PLAFOND is specified.
    # This is the upper limit bracket
    if plafond:
        rates.append(to_vector(0, nb_entities))
        thresholds.append(to_vector(1, nb_entities))

    return tax_scale.calc(base, factor, thresholds=thresholds, rates=rates)



def compute_scales(parameter, base_options):
    bareme = parameter.get('BAREME')
    base, factor = certify_base_options(base_options)

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
    return tax_scale.calc(base, factor, thresholds=thresholds, rates=rates)


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
