from __future__ import annotations

from typing import Sequence, Generator, Optional, cast
from openfisca_core.types import (
    TaxBenefitSystemType,
    OptionsSchema,
    TestSchema,
    )

import os
import traceback

from _pytest.python import Package
from py._path.local import LocalPath
from pytest import File

from ._yaml import yaml, Loader
from ._yaml_item import YamlItem


class YamlFile(File):

    def __init__(
            self,
            path: LocalPath,
            fspath: LocalPath,
            parent: Package,
            tax_benefit_system: TaxBenefitSystemType,
            options: OptionsSchema,
            ) -> None:

        super(YamlFile, self).__init__(path, parent)
        self.tax_benefit_system = tax_benefit_system
        self.options = options

    def collect(self) -> Generator[YamlItem, None, None]:
        tests: Sequence[TestSchema]

        try:
            tests = yaml.load(self.fspath.open(), Loader = Loader)
        except (yaml.scanner.ScannerError, yaml.parser.ParserError, TypeError):
            message = os.linesep.join([
                traceback.format_exc(),
                f"'{self.fspath}' is not a valid YAML file. Check the stack trace above for more details.",
                ])
            raise ValueError(message)

        if not isinstance(tests, list):
            tests = cast(Sequence[TestSchema], [tests])

        for test in tests:
            if not self.should_ignore(test):
                yield YamlItem.from_parent(self,
                    name = '',
                    baseline_tax_benefit_system = self.tax_benefit_system,
                    test = test, options = self.options)

    def should_ignore(self, test: TestSchema) -> bool:
        name_filter: Optional[str] = self.options.get('name_filter')
        stem: str = os.path.splitext(self.fspath.basename)[0]
        name: str = test.get('name', '')
        kwds: Sequence[str] = test.get('keywords', [])

        return (
            name_filter is not None
            and name_filter not in stem
            and name_filter not in name
            and name_filter not in kwds
            )
