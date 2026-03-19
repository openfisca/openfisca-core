from __future__ import annotations

from typing import Any

from openfisca_core.types import TaxBenefitSystem

from openfisca_core.parameters.parameter_node import ParameterNode
from openfisca_core.reforms import Reform


class InYamlTestReform(Reform):
    """A class representing a parametric reform directly defined in YAML test files."""

    def __init__(
        self,
        baseline: TaxBenefitSystem,
        reformed_parameters: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the InYamlTestReform instance.

        :param baseline: Baseline TaxBenefitSystem.
        :param reformed_parameters:
            YAML test file `parameters` value, shaped like a parameter tree.
            This reform replaces the full parameter tree with this value.
        """
        self.reformed_parameters = reformed_parameters or {}
        super().__init__(baseline)

    def apply(self):
        def modify_parameters(_local_parameters: ParameterNode) -> ParameterNode:
            return ParameterNode(data=self.reformed_parameters)

        self.modify_parameters(modifier_function=modify_parameters)
