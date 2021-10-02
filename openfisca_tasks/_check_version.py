from __future__ import annotations

import textwrap
from typing import Optional, Sequence, Type, Tuple

from openfisca_core.indexed_enums import Enum

from . import SupportsProgress

from ._contract_builder import Contract, ContractBuilder
from ._repo import Repo

IGNORE_DIFF_ON: Sequence[str]
IGNORE_DIFF_ON = (
    ".circleci",
    ".github",
    ".gitignore",
    ".mk",
    "CONTRIBUTING.md",
    "LICENSE",
    "Makefile",
    "README.md",
    "STYLEGUIDE.md",
    "tests",
    )


class Exit(Enum):
    OK = "ok"
    KO = "ko"


class Version(Enum):
    NONE = "none"
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"


class CheckVersion:
    exit: int
    repo: Repo
    actual: Sequence[Contract]
    actual_files: Sequence[str]
    actual_version: str
    before: Sequence[Contract]
    before_files: Sequence[str]
    before_version: str
    changed_files: Sequence[str]
    contracts: Sequence[Contract]
    files: Sequence[str]
    progress: SupportsProgress
    required: int
    version: int

    def __init__(self, repo_type: Type[Repo] = Repo):
        self.exit = Exit.OK.index
        self.repo = Repo()
        self.changed_files = self.repo.files.changed()
        self.actual_files = self.repo.files.actual()
        self.before_files = self.repo.files.before()
        self.actual_version = self.repo.version.actual()
        self.before_version = self.repo.version.before()
        self.version = Version.NONE.index

    def __call__(self, progress: SupportsProgress) -> None:
        self.progress = progress
        self.actual = self._parse_actual()
        self.before = self._parse_before()

        if self._has_changes():
            self.exit = Exit.KO.index

        if self._has_added_functions():
            self.exit = Exit.KO.index

        if self._has_removed_functions():
            self.exit = Exit.KO.index

        self.required = tuple(Version)[self.version].value

        self.progress.info(f"Version bump required: {self.required}!\n")
        self.progress.okay(f"Current version: {self.actual_version}")

        if self._is_version_acceptable():
            self.exit = Exit.OK.index

        if self.exit == Exit.KO.index:
            self.progress.fail()

        self.progress.next()

    def _has_changes(self) -> bool:
        total: int
        total = len(self.changed_files)

        self.progress.info("Checking for functional changes…\n")
        self.progress.init()

        for count, file in enumerate(self.changed_files):
            if not self._is_functional(file):
                continue

            self.version = max(self.version, Version.PATCH.index)
            self.progress.wipe()
            self.progress.warn(f"~ {file}\n")

            self.progress.push(count, total)

        self.progress.wipe()
        return bool(self.version)

    def _has_added_functions(self) -> bool:
        actual = set(contract.name for contract in self.actual)
        before = set(contract.name for contract in self.before)

        added = actual ^ before & actual
        total = len(added)

        self.progress.info("Checking for added functions…\n")
        self.progress.init()

        for count, name in enumerate(added):
            contract = self._find(name, self.actual)

            if contract is None or not self._is_functional(contract.file):
                continue

            self.version = max(self.version, Version.MINOR.index)
            self.progress.wipe()
            self.progress.warn(f"+ {contract.name}\n")
            self.progress.push(count, total)

        self.progress.wipe()
        return bool(self.version)

    def _has_removed_functions(self) -> bool:
        actual = set(contract.name for contract in self.actual)
        before = set(contract.name for contract in self.before)

        removed = (before ^ actual & before)
        total = len(removed)

        self.progress.info("Checking for removed functions…\n")
        self.progress.init()

        for count, name in enumerate(removed):
            contract = self._find(name, self.before)

            if contract is None or not self._is_functional(contract.file):
                continue

            self.version = max(self.version, Version.MAJOR.index)
            self.progress.wipe()
            self.progress.warn(f"- {contract.name}\n")
            self.progress.push(count, total)

        self.progress.wipe()
        return bool(self.version)

    def _is_functional(self, file: str) -> bool:
        return not any(exclude in file for exclude in IGNORE_DIFF_ON)

    def _is_version_acceptable(self) -> bool:
        if self.version == Version.NONE.index:
            return True

        actual = self.actual_version.split(".")[::-1]
        before = self.before_version.split(".")[::-1]

        if int(actual[self.version - 1]) >= int(before[self.version - 1]) + 1:
            return True

        return False

    def _find(self, name: str, pool: Sequence[Contract]) -> Optional[Contract]:
        return next(
            (
                contract
                for contract in pool
                if contract.name == name
                ),
            None,
            )

    def _parse_actual(self) -> Tuple[Contract, ...]:
        builder: ContractBuilder
        source: str

        builder = ContractBuilder(self.actual_files)

        self.progress.info("Parsing files from the current branch…\n")
        self.progress.init()

        for file in builder.files:
            with open(file, "r") as f:
                source = textwrap.dedent(f.read())
                builder(source)
                self.progress.push(builder.count, builder.total)

        self.progress.wipe()

        return builder.contracts

    def _parse_before(self) -> Tuple[Contract, ...]:
        builder: ContractBuilder
        content: str
        source: str

        builder = ContractBuilder(self.before_files)

        self.progress.info(f"Parsing files from {self.before_version}…\n")
        self.progress.init()

        for file in builder.files:
            content = self.repo.files.show(file)
            source = textwrap.dedent(content)
            builder(source)
            self.progress.push(builder.count, builder.total)

        self.progress.wipe()

        return builder.contracts
