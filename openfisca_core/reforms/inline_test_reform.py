from __future__ import annotations

from typing import IO, Iterator

from openfisca_core.types import TaxBenefitSystem
from openfisca_core.parameters.parameter_node import ParameterNode
from openfisca_core.reforms import Reform


class InlineTestReform(Reform):
    """A class representing a reform defined in an Excel file.

    This class extends the Reform class to provide functionality specific to reforms defined in Excel format.
    """

    def __init__(
        self,
        baseline: TaxBenefitSystem,
        reformed_parameters = None,
    ) -> None:
        """Initialize the ReformExcel instance.

        :param baseline: Baseline TaxBenefitSystem.
        :param path: Path to the Excel file defining the reform.
        :param suffix: Suffix to identify the relevant parameters sheet.
        """
        self.reformed_parameters = reformed_parameters or []
        super().__init__(baseline)

    def apply(self):
        def modify_parameters(local_parameters: ParameterNode) -> ParameterNode:
            return ParameterNode(data=self.reformed_parameters)

        self.modify_parameters(modifier_function=modify_parameters)
