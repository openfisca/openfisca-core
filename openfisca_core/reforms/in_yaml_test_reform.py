from __future__ import annotations

from openfisca_core.types import TaxBenefitSystem

from openfisca_core.parameters.parameter_node import ParameterNode
from openfisca_core.reforms import Reform


class InYamlTestReform(Reform):
    """A class representing a parametric reform directly defined in YAML test files."""

    def __init__(
        self,
        baseline: TaxBenefitSystem,
        reformed_parameters=dict,
    ) -> None:
        """Initialize the ReformExcel instance.

        :param baseline: Baseline TaxBenefitSystem.
        :param reformed_parameters: Yaml file `parameters` value similar to a parameter tree
        """
        self.reformed_parameters = reformed_parameters
        super().__init__(baseline)

    def apply(self):
        def modify_parameters(local_parameters: ParameterNode) -> ParameterNode:
            return ParameterNode(data=self.reformed_parameters)

        self.modify_parameters(modifier_function=modify_parameters)
