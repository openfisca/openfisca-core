from openfisca_core.parameters import ParameterNode


class ParameterScaleBracket(ParameterNode, dict):
    """
    A parameter scale bracket.
    """

    _allowed_keys = set(['amount', 'threshold', 'rate', 'average_rate', 'base'])
