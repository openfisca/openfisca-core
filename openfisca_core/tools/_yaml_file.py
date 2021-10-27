from __future__ import annotations

from typing import Sequence

import os
import traceback

import pytest

from openfisca_core.cases import Case

from ._yaml import yaml, Loader
from ._yaml_item import YamlItem


class YamlFile(pytest.File):

    def __init__(self, path, fspath, parent, tax_benefit_system, options):
        super(YamlFile, self).__init__(path, parent)
        self.tax_benefit_system = tax_benefit_system
        self.options = options

    def collect(self):
        tests: Sequence[Case]

        try:
            tests = yaml.load(self.fspath.open(), Loader = Loader)
        except (yaml.scanner.ScannerError, yaml.parser.ParserError, TypeError):
            message = os.linesep.join([
                traceback.format_exc(),
                f"'{self.fspath}' is not a valid YAML file. Check the stack trace above for more details.",
                ])
            raise ValueError(message)

        if not isinstance(tests, list):
            tests = [tests]

        for test in tests:
            if not self.should_ignore(test):
                yield YamlItem.from_parent(self,
                    name = '',
                    baseline_tax_benefit_system = self.tax_benefit_system,
                    test = test, options = self.options)

    def should_ignore(self, test):
        name_filter = self.options.get('name_filter')
        return (
            name_filter is not None
            and name_filter not in os.path.splitext(self.fspath.basename)[0]
            and name_filter not in test.get('name', '')
            and name_filter not in test.get('keywords', [])
            )
