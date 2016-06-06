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
        raise legislations.ParameterNotFound(instant=instant, name=name)

    # select and set the right value for this instant
    transform_dict_key(
        parameter,
        dict(key_to_find='values', new_key='value',
             transform=lambda values: choose_temporal_value(name, values, instant)),
        )

    # filter VAR cases using variables
    # remember : we're working on vector variables
    univoque_parameter = resolve_var_cases(vector_variables, parameter)

    # Now apply specific computations if any : marginalRateTaxScale, linear...
    value = compute_parameter(univoque_parameter, base_options)

    # A vector should be returned here. Explicitely build one of the right dimension
    # in case it wasn't created (e.g. based on base_options.base)
    return np.zeros(dimension) + value if not isinstance(value, np.ndarray) else value


def compute_parameter(parameter, base_options):
    if parameter.get('marginalRateTaxScale'):
        return compute_scales(parameter, base_options)
    if parameter.get('linear'):
        return compute_linear(parameter, base_options)
    if parameter.get('value') is not None:
        return parameter['value']
    else:
        # TODO don't raise general Exception !
        raise Exception(
            'Absent or unknown computation type for this parameter'
            )


def transform_dict_key(node, options, parent_node=None, parent_key=None):
    if isinstance(node, list):
        [transform_dict_key(element, options) for element in node]
    if isinstance(node, dict):
        for key, value in node.items():
            if key == options['key_to_find']:
                if options.get('replace_parent'):
                    if parent_node is None:
                        node.update(options['transform'](value))
                    else:
                        parent_node[parent_key] = options['transform'](value)
                elif options.get('new_key'):
                    node[options['new_key']] = options['transform'](value)
                    del node[options['key_to_find']]
            else:
                transform_dict_key(value, options, node, key)


def convert_value_date(date):
    return conv.date_to_iso8601_str(date)[0]


def choose_temporal_value(name, values, instant):
    str_instant = str(instant)

    # Prepare the error
    error = legislations.ParameterNotFound(instant=instant, name=name)

    if isinstance(values, dict):
        #  Simple object date notation
        for raw_date in sorted(values, reverse=True):
            date = convert_value_date(raw_date)
            if str_instant >= date:
                return values[raw_date]
        raise error

    elif isinstance(values, list):
        # Complete object list notation

        for value in values:
            beginning = convert_value_date(value['deb'])
            end = convert_value_date(value['fin']) if value.get('fin') else None

            if end is None and value.get('fuzzy') is None:
                # TODO don't raise general Exception !
                raise Exception(
                    'Please set a "fin" date or set "fuzzy" to true in your parameters')

            if beginning <= str(instant) and (end is None or str(instant) <= end):
                return value['valeur']

    raise error


def get_parameter_value(node, attribute, default=None):
    value = node.get(attribute)
    if value:
        return value['value']
    else:
        assert default is not None
        return default


def to_vector(element, vector_size):
    if isinstance(element, (int, float)):
        vector = np.empty(vector_size)
        vector.fill(element)
        return vector
    return element


def certify_base(base_options):
    assert base_options is not None
    base = base_options.get('base', None)
    factor = base_options.get('factor')
    assert base is not None
    return base, factor


def compute_linear(parameter, base_options):
    linear = parameter.get('linear')
    base, factor = certify_base(base_options)
    limit = linear.get('limit')

    # Construct a taxscale (see def compute_scales)

    thresholds = list()
    rates = list()
    nb_entities = len(base)
    tax_scale = taxscales.MarginalRateTaxScale(name=parameter.get('variable'))

    # With one bracket only...
    rates.append(to_vector(linear['value'], nb_entities))
    thresholds.append(to_vector(0, nb_entities))

    # ... or two if limit is specified.
    # This is the upper limit bracket
    if limit:
        rates.append(to_vector(0, nb_entities))
        thresholds.append(to_vector(1, nb_entities))

    return tax_scale.calc(base, factor, thresholds=thresholds, rates=rates)


def compute_scales(parameter, base_options):
    # Only the case of the MarginalRateTaxScale is supported in YAML parameters
    scale = parameter.get('marginalRateTaxScale')
    base, factor = certify_base(base_options)

    nb_entities = len(base)
    thresholds = list()
    rates = list()
    # Construct the tax scale
    tax_scale = taxscales.MarginalRateTaxScale(name=parameter.get('variable'))
    for bracket in scale:
        rate = get_parameter_value(bracket, 'rate')
        threshold = get_parameter_value(bracket, 'threshold')
        # transform scalar to vector
        rates.append(to_vector(rate, nb_entities))
        thresholds.append(to_vector(threshold, nb_entities))
    return tax_scale.calc(base, factor, thresholds=thresholds, rates=rates)


def resolve_var_cases(vector_variables, parameter):
    parameter_copy = copy.deepcopy(parameter)
    transform_dict_key(
        parameter_copy,
        dict(key_to_find='var', replace_parent=True,
             transform=lambda cases: choose_conditional_case(cases, vector_variables)),
        )

    return parameter_copy


def choose_conditional_case(cases, variables):
    # The first value whose case is evaluated to true is selected (for each entity of our entity vector)
    case_conditions = np.array([resolve_condition(case['condition'], variables) for case in cases])
    case_values = [case['value'] for case in cases]
    return {
        'value': np.select(case_conditions, case_values)
        }


def resolve_condition(condition_string, variables):
    return eval(condition_string, variables)
