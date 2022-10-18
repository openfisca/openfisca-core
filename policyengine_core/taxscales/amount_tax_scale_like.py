import abc
import bisect
import os
import typing

from policyengine_core import tools
from policyengine_core.taxscales.tax_scale_like import TaxScaleLike


class AmountTaxScaleLike(TaxScaleLike, abc.ABC):
    """
    Base class for various types of amount-based tax scales: single amount,
    marginal amount...
    """

    amounts: typing.List

    def __init__(
        self,
        name: typing.Optional[str] = None,
        option: typing.Any = None,
        unit: typing.Any = None,
    ) -> None:
        super().__init__(name, option, unit)
        self.amounts = []

    def __repr__(self) -> str:
        return tools.indent(
            os.linesep.join(
                [
                    f"- threshold: {threshold}{os.linesep}  amount: {amount}"
                    for (threshold, amount) in zip(
                        self.thresholds, self.amounts
                    )
                ]
            )
        )

    def add_bracket(
        self,
        threshold: int,
        amount: typing.Union[int, float],
    ) -> None:
        if threshold in self.thresholds:
            i = self.thresholds.index(threshold)
            self.amounts[i] += amount

        else:
            i = bisect.bisect_left(self.thresholds, threshold)
            self.thresholds.insert(i, threshold)
            self.amounts.insert(i, amount)

    def to_dict(self) -> dict:
        return {
            str(threshold): self.amounts[index]
            for index, threshold in enumerate(self.thresholds)
        }
