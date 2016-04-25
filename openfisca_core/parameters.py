from . import conv

# Helpers to access, set and transform dict values


def get_from_dict(data_dict, map_list):
    return reduce(lambda d, k: d[k], map_list, data_dict)


def set_in_dict(data_dict, map_list, value):
    get_from_dict(data_dict, map_list[:-1])[map_list[-1]] = value


def look_for_and_choose_values_rec(node, instant):
    for key, value in node.items():

        if isinstance(value, dict):
            if value.get('VALUES'):
                node[key] = choose_value(value.get('VALUES'), instant)
            else:
                look_for_and_choose_values_rec(value, instant)
        if isinstance(value, list):
            [look_for_and_choose_values_rec(element, instant) for element in value]


def convert_value_date(date):
    return conv.date_to_iso8601_str(date)[0]


def choose_value(values, instant):
    for value in values:
        beginning = convert_value_date(value['deb'])
        end = convert_value_date(value['fin']) if value.get('fin') else None

        if end is None and value.get('fuzzy') is None:
            raise Exception('Please set a "fin" date or set "fuzzy" to true in your parameters') #TODO don't raise general Exception !

        if beginning <= instant and (end is None or instant <= end):
            return value['valeur']

    return None


def get_parameter(parameters, collection, variable, instant, variables=None):

    # Get the requested parameter from the requested collection
    parameter = next((x for x in parameters[collection] if x['variable'] == variable), None)
    if parameter is None:
        message = "Parameter \"{0}\" not found in collection \"{1}\"".format(variable, collection)
        raise Exception(message) #TODO don't raise general Exception !

    # select and set the right value for this instant

    look_for_and_choose_values_rec(parameters, instant)

    # filter VAR cases using variables
    print 'parameter valued'
    print parameter
    # generate scales
    return parameter


