from __future__ import annotations

from ._yaml_file import YamlFile


class YamlPlugin:

    def __init__(self, tax_benefit_system, options):
        self.tax_benefit_system = tax_benefit_system
        self.options = options

    def pytest_collect_file(self, parent, path):
        """
        Called by pytest for all plugins.
        :return: The collector for test methods.
        """
        if path.ext in [".yaml", ".yml"]:
            return YamlFile.from_parent(
                parent,
                path = path,
                fspath = path,
                tax_benefit_system = self.tax_benefit_system,
                options = self.options,
                )
