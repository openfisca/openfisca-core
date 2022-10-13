import copy
import os
import typing
from typing import Any, Iterable
from policyengine_core import commons, parameters, tools
from policyengine_core.errors import ParameterParsingError
from policyengine_core.parameters import config, helpers, AtInstantLike
from policyengine_core.periods.instant_ import Instant
from policyengine_core.taxscales import (
    LinearAverageRateTaxScale,
    MarginalAmountTaxScale,
    MarginalRateTaxScale,
    SingleAmountTaxScale,
    TaxScaleLike,
)


class ParameterScale(AtInstantLike):
    """
    A parameter scale (for instance a  marginal scale).
    """

    # 'unit' and 'reference' are only listed here for backward compatibility
    _allowed_keys = config.COMMON_KEYS.union({"brackets"})

    def __init__(self, name: str, data: dict, file_path: str):
        """
        :param name: name of the scale, eg "taxes.some_scale"
        :param data: Data loaded from a YAML file. In case of a reform, the data can also be created dynamically.
        :param file_path: File the parameter was loaded from.
        """
        self.name: str = name
        self.file_path: str = file_path
        helpers._validate_parameter(
            self, data, data_type=dict, allowed_keys=self._allowed_keys
        )
        self.description: str = data.get("description")
        self.metadata: typing.Dict = {}
        self.metadata.update(data.get("metadata", {}))

        if not isinstance(data.get("brackets", []), list):
            raise ParameterParsingError(
                "Property 'brackets' of scale '{}' must be of type array.".format(
                    self.name
                ),
                self.file_path,
            )

        brackets = []
        for i, bracket_data in enumerate(data.get("brackets", [])):
            bracket_name = helpers._compose_name(name, item_name=i)
            bracket = parameters.ParameterScaleBracket(
                name=bracket_name, data=bracket_data, file_path=file_path
            )
            brackets.append(bracket)
        self.brackets: typing.List[parameters.ParameterScaleBracket] = brackets

    def __getitem__(self, key: str) -> Any:
        if isinstance(key, int) and key < len(self.brackets):
            return self.brackets[key]
        else:
            raise KeyError(key)

    def __repr__(self) -> str:
        return os.linesep.join(
            ["brackets:"]
            + [
                tools.indent("-" + tools.indent(repr(bracket))[1:])
                for bracket in self.brackets
            ]
        )

    def get_descendants(self) -> Iterable:
        return iter(())

    def clone(self) -> "ParameterScale":
        clone = commons.empty_clone(self)
        clone.__dict__ = self.__dict__.copy()

        clone.brackets = [bracket.clone() for bracket in self.brackets]
        clone.metadata = copy.deepcopy(self.metadata)

        return clone

    def _get_at_instant(self, instant: Instant) -> TaxScaleLike:
        brackets = [
            bracket.get_at_instant(instant) for bracket in self.brackets
        ]

        if self.metadata.get("type") == "single_amount":
            scale = SingleAmountTaxScale()
            for bracket in brackets:
                if (
                    "amount" in bracket._children
                    and "threshold" in bracket._children
                ):
                    amount = bracket.amount
                    threshold = bracket.threshold
                    scale.add_bracket(threshold, amount)
            return scale
        elif any("amount" in bracket._children for bracket in brackets):
            scale = MarginalAmountTaxScale()
            for bracket in brackets:
                if (
                    "amount" in bracket._children
                    and "threshold" in bracket._children
                ):
                    amount = bracket.amount
                    threshold = bracket.threshold
                    scale.add_bracket(threshold, amount)
            return scale
        elif any("average_rate" in bracket._children for bracket in brackets):
            scale = LinearAverageRateTaxScale()

            for bracket in brackets:
                if "base" in bracket._children:
                    base = bracket.base
                else:
                    base = 1.0
                if (
                    "average_rate" in bracket._children
                    and "threshold" in bracket._children
                ):
                    average_rate = bracket.average_rate
                    threshold = bracket.threshold
                    scale.add_bracket(threshold, average_rate * base)
            return scale
        else:
            scale = MarginalRateTaxScale()

            for bracket in brackets:
                if "base" in bracket._children:
                    base = bracket.base
                else:
                    base = 1.0
                if (
                    "rate" in bracket._children
                    and "threshold" in bracket._children
                ):
                    rate = bracket.rate
                    threshold = bracket.threshold
                    scale.add_bracket(threshold, rate * base)
            return scale
