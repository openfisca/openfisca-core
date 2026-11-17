from openfisca_core.parameters import ParameterNode


class ParameterScaleBracket(ParameterNode):
    """A parameter scale bracket."""

    _allowed_keys = {"threshold", "average_rate"}


class ParameterAverageRateScaleBracket(ParameterNode):
    """A parameter scale bracket."""

    _allowed_keys = {"threshold", "average_rate"}


class ParameterMarginalRateScaleBracket(ParameterNode):
    """A parameter scale bracket."""

    _allowed_keys = {"threshold", "rate"}


class ParameterAmountScaleBracket(ParameterNode):
    """A parameter scale bracket."""

    _allowed_keys = {"threshold", "amount"}
