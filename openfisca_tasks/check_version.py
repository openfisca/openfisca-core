from __future__ import annotations

from typing import Sequence, Set, TypeVar

from openfisca_core.indexed_enums import Enum

from . import SupportsProgress

from ._builder import Contract
from ._bumper import Bumper
from ._parser import Parser
from ._protocols import HasIndex, SupportsParsing

T = TypeVar("T", bound = "CheckVersion")

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


class CheckVersion:
    """Checks if the current version is acceptable."""

    exit: HasIndex
    progress: SupportsProgress

    def __init__(self) -> None:
        self.exit = Exit.OK

    def __call__(self, progress: SupportsProgress) -> None:
        before: Set[Contract]
        actual: Set[Contract]
        files: Set[str]

        self.progress = progress

        bumper = Bumper()
        parser = Parser()
        actual = set(self._parse(parser.actual, "HEAD"))
        before = set(self._parse(parser.before, bumper.before))
        files = set(parser.changed_files)

        (
            self
            ._check_files(bumper, files)
            ._check_funcs(bumper, "added", actual, before)
            ._check_funcs(bumper, "removed", before, actual)
            ._check_version_acceptable(bumper)
            )

    def _parse(self, parser: SupportsParsing, rev: str) -> Sequence[Contract]:
        self.progress.info(f"Parsing files from {rev}…\n")
        self.progress.init()

        with parser as parsing:
            for count, total in parsing:
                self.progress.push(count, total)

        self.progress.wipe()
        return parser.contracts

    def _check_files(self: T, bumper: Bumper, files: Set[str]) -> T:
        what: str = "diff"
        total: int = len(files)

        self.progress.info("Checking for functional changes…\n")
        self.progress.init()

        for count, file in enumerate(files):
            if not self._is_functional(file):
                continue

            bumper(what)
            self.exit = Exit.KO
            self.progress.wipe()
            self.progress.warn(f"{str(bumper.what(what))} {file}\n")
            self.progress.push(count, total)

        self.progress.wipe()

        return self

    def _check_funcs(
            self: T,
            bumper: Bumper,
            what: str,
            *files: Set[Contract],
            ) -> T:

        diff: Set[Contract] = files[0] ^ files[1] & files[0]
        total: int = len(diff)

        self.progress.info(f"Checking for {what} functions…\n")
        self.progress.init()

        for count, contract in enumerate(diff):
            if contract is None or not self._is_functional(contract.file):
                continue

            bumper(what)
            self.exit = Exit.KO
            self.progress.wipe()
            self.progress.warn(f"{str(bumper.what(what))} {contract.name}\n")
            self.progress.push(count, total)

        self.progress.wipe()

        return self

    def _check_version_acceptable(self, bumper: Bumper) -> None:
        self.progress.info(f"Version bump required: {bumper.required.name}!\n")
        self.progress.okay(f"Current version: {bumper.actual}")

        if bumper.is_acceptable():
            self.exit = Exit.OK
        else:
            self.progress.fail()

        self.progress.then()

    def _is_functional(self, file: str) -> bool:
        return not any(exclude in file for exclude in IGNORE_DIFF_ON)
