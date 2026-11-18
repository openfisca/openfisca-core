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
        super().__init__(name, directory_path, data, file_path)
        message = [
            "The 'amount' bracket should be replaced by 'single_amount'.",
            "Relying on metadata.type is deprecated since version 47.0.0",
            "and will be removed in the future.",
        ]
        warnings.warn(" ".join(message), DeprecationWarning, stacklevel=2)


def ParameterScaleBracket(name="", directory_path=None, data=None, file_path=None):
    generic_message = [
        "ParameterScaleBracket is deprecated since version 47.0.0",
        "and will be removed in the future.",
        "ParameterScaleBracket should be replaced by specific bracket classes Parameter*Bracket.",
    ]
    if "rate" in data:
        message = [
            *generic_message,
            "In the specific call by 'ParameterMarginalRateScaleBracket'.",
        ]
        warnings.warn(" ".join(message), DeprecationWarning, stacklevel=2)
        return ParameterMarginalRateScaleBracket(name, directory_path, data, file_path)
    elif "average_rate" in data:
        message = [
            *generic_message,
            "In the specific call by 'ParameterAverageRateScaleBracket'.",
        ]
        warnings.warn(" ".join(message), DeprecationWarning, stacklevel=2)
        return ParameterAverageRateScaleBracket(name, directory_path, data, file_path)
    elif "amount" in data:
        message = [
            *generic_message,
            "In the specific call by 'ParameterMarginalAmountScaleBracket'.",
        ]
        warnings.warn(" ".join(message), DeprecationWarning, stacklevel=2)
        return ParameterMarginalAmountScaleBracket(
            name, directory_path, data, file_path
        )

    msg = "The relevant ParameterScaleBracket class could not be determined from the provided data."
    raise ValueError(msg)
