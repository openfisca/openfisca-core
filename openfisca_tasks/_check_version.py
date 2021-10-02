from __future__ import annotations

from typing import Sequence, Type

from openfisca_core.indexed_enums import Enum

from . import SupportsProgress

from ._contract_builder import Contract
from ._file_parser import FileParser
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
    """Checks if the current version is acceptable."""

    exit: int
    repo: Repo
    actual: Sequence[Contract]
    actual_version: str
    before: Sequence[Contract]
    before_version: str
    contracts: Sequence[Contract]
    files: Sequence[str]
    progress: SupportsProgress
    required: int
    version: int

    def __init__(self, repo_type: Type[Repo] = Repo):
        self.exit = Exit.OK.index
        self.repo = Repo()
        self.actual_version = self.repo.versions.actual()
        self.before_version = self.repo.versions.before()
        self.version = Version.NONE.index
        self.parser = FileParser()

    def __call__(self, progress: SupportsProgress) -> None:
        self.progress = progress

        self.progress.info("Parsing files from the current branch…\n")
        self.progress.init()

        with self.parser.actual as parser:
            for count, total in parser:
                self.progress.push(count, total)

            self.progress.wipe()

        self.progress.info(f"Parsing files from {self.before_version}…\n")
        self.progress.init()

        with self.parser.before as parser:
            for count, total in parser:
                self.progress.push(count, total)

            self.progress.wipe()

        self.actual = self.parser.actual.contracts
        self.before = self.parser.before.contracts

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
        total = len(self.parser.changed_files)

        self.progress.info("Checking for functional changes…\n")
        self.progress.init()

        for count, file in enumerate(self.parser.changed_files):
            if not self._is_functional(file):
                continue

            self.version = max(self.version, Version.PATCH.index)
            self.progress.wipe()
            self.progress.warn(f"~ {file}\n")

            self.progress.push(count, total)

        self.progress.wipe()
        return bool(self.version)

    def _has_added_functions(self) -> bool:
        actual = set(self.actual)
        before = set(self.before)

        added = actual ^ before & actual
        total = len(added)

        self.progress.info("Checking for added functions…\n")
        self.progress.init()

        for count, contract in enumerate(added):

            if contract is None or not self._is_functional(contract.file):
                continue

            self.version = max(self.version, Version.MINOR.index)
            self.progress.wipe()
            self.progress.warn(f"+ {contract.name}\n")
            self.progress.push(count, total)

        self.progress.wipe()
        return bool(self.version)

    def _has_removed_functions(self) -> bool:
        actual = set(self.actual)
        before = set(self.before)

        removed = (before ^ actual & before)
        total = len(removed)

        self.progress.info("Checking for removed functions…\n")
        self.progress.init()

        for count, contract in enumerate(removed):

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
