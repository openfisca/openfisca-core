import warnings

from openfisca_core.parameters import ParameterNode


class ParameterAverageRateScaleBracket(ParameterNode):
    _value_key = "average_rate"
    _allowed_keys = {"threshold", _value_key}


class ParameterMarginalRateScaleBracket(ParameterNode):
    _value_key = "rate"
    _allowed_keys = {"threshold", _value_key}


class ParameterMarginalAmountScaleBracket(ParameterNode):
    _value_key = "amount"
    _allowed_keys = {"threshold", _value_key}


class ParameterSingleAmountScaleBracket(ParameterNode):
    _value_key = "single_amount"
    _allowed_keys = {"threshold", _value_key}


class LegacyParameterSingleAmountScaleBracket(ParameterNode):
    _value_key = "amount"
    _allowed_keys = {"threshold", _value_key}

    def __init__(self, name="", directory_path=None, data=None, file_path=None) -> None:
        message = [
            "The 'amount' bracket should be replaced by 'single_amount'",
            "version XXX, and will be removed in the future.",
        ]
        warnings.warn(" ".join(message), DeprecationWarning, stacklevel=2)
        super().__init__(name, directory_path, data, file_path)
