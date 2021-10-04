from __future__ import annotations

from typing import Sequence, Set, TypeVar

from openfisca_core.indexed_enums import Enum

from . import SupportsProgress

from ._builder import Contract
from ._bumper import Bumper
from ._parser import Parser
from ._protocols import HasFiles, HasIndex, SupportsParsing

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
    """An enum with exit codes."""

    OK = "ok"
    KO = "ko"


class CheckVersion:
    """Checks if the current version is acceptable.

    Attributes:
        exit: An exit code.
        progress: A progress bar.
        parser: A file parser.
        bumper: A version bumper.

    .. versionadded:: 36.1.0

    """

    exit: HasIndex
    progress: SupportsProgress
    parser: HasFiles
    bumper: Bumper

    def __init__(
            self,
            progress: SupportsProgress,
            *,
            parser: HasFiles = Parser(),
            ) -> None:
        self.exit = Exit.OK
        self.progress = progress
        self.parser = parser
        self.bumper = Bumper()

    def __call__(self) -> None:
        """Runs all the checks."""

        before: Set[Contract]
        actual: Set[Contract]
        files: Set[str]

        actual = set(self._parse(self.parser.actual, "HEAD"))
        before = set(self._parse(self.parser.before, self.bumper.before))
        files = set(self.parser.changed_files)

        (
            self
            ._check_files(self.bumper, files)
            ._check_funcs(self.bumper, "added", actual, before)
            ._check_funcs(self.bumper, "removed", before, actual)
            ._check_version_acceptable(self.bumper)
            .progress
            .then()
            )

    def _parse(self, parser: SupportsParsing, rev: str) -> Sequence[Contract]:
        """Updates status while the parser builds contracts."""

        self.progress.info(f"Parsing files from {rev}…\n")
        self.progress.init()

        with parser as parsing:
            for count, total in parsing:
                self.progress.push(count, total)

        self.progress.wipe()
        return parser.contracts

    def _check_files(self: T, bumper: Bumper, files: Set[str]) -> T:
        """Requires a bump if there's a diff in files."""

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
        """Requires a bump if there's a diff in functions."""

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

    def _check_version_acceptable(self: T, bumper: Bumper) -> T:
        """Requires a bump if there current version is not acceptable."""

        self.progress.info(f"Version bump required: {bumper.required.name}!\n")
        self.progress.okay(f"Current version: {bumper.actual}")

        if bumper.is_acceptable():
            self.exit = Exit.OK
            return self

        self.progress.fail()

        return self

    def _is_functional(self, file: str) -> bool:
        """Checks if a given ``file`` is whitelisted as functional."""

        return not any(exclude in file for exclude in IGNORE_DIFF_ON)
