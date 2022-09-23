from .parameter_node import ParameterNode


class ParameterScaleBracket(ParameterNode):
    """
    A parameter scale bracket.
    """

    _allowed_keys = {"amount", "threshold", "rate", "average_rate", "base"}
