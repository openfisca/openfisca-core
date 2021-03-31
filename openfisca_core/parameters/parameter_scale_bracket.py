from openfisca_core import parameters


class ParameterScaleBracket(parameters.ParameterNode):
    """
    A parameter scale bracket.
    """

    _allowed_keys = set(['amount', 'threshold', 'rate', 'average_rate', 'base'])
