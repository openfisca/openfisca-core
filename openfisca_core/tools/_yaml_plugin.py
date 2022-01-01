from __future__ import annotations

from typing import Optional
from openfisca_core.typing import TaxBenefitSystemProtocol, OptionsSchema

from _pytest.main import Session
from py._path.local import LocalPath

from ._yaml_file import YamlFile


class YamlPlugin:

    def __init__(
            self,
            tax_benefit_system: TaxBenefitSystemProtocol,
            options: OptionsSchema,
            ) -> None:

        self.tax_benefit_system = tax_benefit_system
        self.options = options

    def pytest_collect_file(
            self,
            parent: Session,
            path: LocalPath,
            ) -> Optional[YamlFile]:
        """
        Called by pytest for all plugins.
        :return: The collector for test methods.
        """

        if path.ext in [".yaml", ".yml"]:
            return YamlFile.from_parent(  # type: ignore
                parent,
                path = path,
                fspath = path,
                tax_benefit_system = self.tax_benefit_system,
                options = self.options,
                )

        return None
