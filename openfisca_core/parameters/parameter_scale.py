import copy
import os

from openfisca_core import commons, tools
from openfisca_core.errors import ParameterParsingError
from openfisca_core.parameters import AtInstantLike, config, helpers
from openfisca_core.parameters.parameter_scale_brackets import (
    LegacyParameterSingleAmountScaleBracket,
    ParameterAverageRateScaleBracket,
    ParameterMarginalAmountScaleBracket,
    ParameterMarginalRateScaleBracket,
    ParameterSingleAmountScaleBracket,
)
from openfisca_core.scales import (
    AverageRateScale,
    MarginalAmountScale,
    MarginalRateScale,
    SingleAmountScale,
)

BRACKET_TYPES = {
    "average_rate": ParameterAverageRateScaleBracket,
    "marginal_amount": ParameterMarginalAmountScaleBracket,
    "marginal_rate": ParameterMarginalRateScaleBracket,
    "single_amount": ParameterSingleAmountScaleBracket,
}

SCALE_TYPES = {
    "average_rate": AverageRateScale,
    "marginal_amount": MarginalAmountScale,
    "marginal_rate": MarginalRateScale,
    "single_amount": SingleAmountScale,
}


class ParameterScale(AtInstantLike):
    """A parameter scale (for instance a  marginal scale)."""

    # 'unit' and 'reference' are only listed here for backward compatibility
    _allowed_keys = config.COMMON_KEYS.union({"brackets"})

    def __init__(self, name, data, file_path) -> None:
        """:param name: name of the scale, eg "taxes.some_scale"
        :param data: Data loaded from a YAML file. In case of a reform, the data can also be created dynamically.
        :param file_path: File the parameter was loaded from.
        """
        self.name: str = name
        self.file_path: str = file_path
        helpers._validate_parameter(
            self,
            data,
            data_type=dict,
            allowed_keys=self._allowed_keys,
        )
        self.description: str = data.get("description")
        self.metadata: dict = {}
        helpers._set_backward_compatibility_metadata(self, data)
        self.metadata.update(data.get("metadata", {}))

        if not isinstance(data.get("brackets", []), list):
            msg = f"Property 'brackets' of scale '{self.name}' must be of type array."
            raise ParameterParsingError(
                msg,
                self.file_path,
            )

        inferred_type = "marginal_rate"
        for bracket in data.get("brackets", []):
            if "rate" in bracket:
                inferred_type = "marginal_rate"
            elif "average_rate" in bracket:
                inferred_type = "average_rate"
            elif "amount" in bracket:
                inferred_type = "marginal_amount"
            elif "single_amount" in bracket:
                inferred_type = "single_amount"
            else:
                msg = f"Brackets of scale '{self.name}' must have a threshold and either an amount, a rate, an average_rate or a single_amount"
                raise ParameterParsingError(msg, self.file_path)
            break

        self._type = inferred_type
        BracketType = BRACKET_TYPES[self._type]
        self.ScaleType = SCALE_TYPES[self._type]
        if (
            self._type != self.metadata.get("type")
            and self.metadata.get("type") == "single_amount"
        ):
            BracketType = LegacyParameterSingleAmountScaleBracket
            self.ScaleType = SingleAmountScale
        self._bracket_value_key = BracketType._value_key

        brackets = []
        for i, bracket_data in enumerate(data.get("brackets", [])):
            bracket_name = helpers._compose_name(name, item_name=i)
            bracket = BracketType(
                name=bracket_name,
                data=bracket_data,
                file_path=file_path,
            )
            brackets.append(bracket)
        self.brackets: list[BracketType] = brackets

    def __getitem__(self, key):
        if isinstance(key, int) and key < len(self.brackets):
            return self.brackets[key]
        raise KeyError(key)

    def __repr__(self) -> str:
        return os.linesep.join(
            ["brackets:"]
            + [
                tools.indent("-" + tools.indent(repr(bracket))[1:])
                for bracket in self.brackets
            ],
        )

    def get_descendants(self):
        return iter(())

    def clone(self):
        clone = commons.empty_clone(self)
        clone.__dict__ = self.__dict__.copy()

        clone.brackets = [bracket.clone() for bracket in self.brackets]
        clone.metadata = copy.deepcopy(self.metadata)

        return clone

    def _get_at_instant(self, instant):
        brackets = [bracket.get_at_instant(instant) for bracket in self.brackets]

        scale = self.ScaleType()
        for bracket in brackets:
            if (
                self._bracket_value_key in bracket._children
                and "threshold" in bracket._children
            ):
                value = bracket[self._bracket_value_key]
                threshold = bracket.threshold
                scale.add_bracket(threshold, value)
        return scale
