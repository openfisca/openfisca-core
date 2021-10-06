from __future__ import annotations

from typing import Optional, Sequence, Set, TypeVar

from openfisca_core.indexed_enums import Enum

from openfisca_tasks import SupportsProgress

from ._builder import Contract
from ._bumper import Bumper
from ._func_checker import FuncChecker
from ._parser import Parser
from ._types import HasIndex, What

T = TypeVar("T", bound = "CheckVersion")

PARSER = Parser(this = "HEAD")

IGNORE = (
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
        bar: A progress bar.
        exit: An exit code.
        parser: A file parser.
        bumper: A version bumper.

    .. versionadded:: 36.1.0

    """

    bar: SupportsProgress
    exit: HasIndex
    parser: Parser
    bumper: Bumper

    def __init__(self, bar: SupportsProgress, parser: Parser = PARSER) -> None:
        self.bar = bar
        self.exit = Exit.OK
        self.parser = parser
        self.bumper = Bumper()

    def __call__(self) -> None:
        """Runs all the checks."""

        this: Set[Contract] = set(self._parse(self.parser, "this"))
        that: Set[Contract] = set(self._parse(self.parser, "that"))
        diff: Set[str] = set(self.parser.diff)

        (
            self
            ._check_files(self.bumper, diff)
            ._check_funcs(self.bumper, "added", this, that)
            ._check_funcs(self.bumper, "removed", that, this)
            ._check_version_acceptable(self.bumper)
            .bar.then()
            )

    def _parse(self, parser: Parser, what: What) -> Sequence[Contract]:
        """Updates status while the parser builds contracts."""

        with parser(what = what) as parsing:
            self.bar.info(f"Parsing files from {parser.current}…\n")
            self.bar.init()

            for count, total in parsing:
                self.bar.push(count, total)

            self.bar.wipe()

        return parser.contracts

    def _check_files(self: T, bumper: Bumper, files: Set[str]) -> T:
        """Requires a bump if there's a diff in files."""

        what: str = "diff"
        total: int = len(files)

        self.bar.info("Checking for functional changes…\n")
        self.bar.init()

        for count, file in enumerate(files):
            if not self._is_functional(file):
                continue

            bumper(what)
            self.exit = Exit.KO
            self.bar.wipe()
            self.bar.warn(f"{str(bumper.what(what))} {file}\n")
            self.bar.push(count, total)

        self.bar.wipe()

        return self

    def _check_funcs(
            self: T,
            bumper: Bumper,
            what: str,
            *files: Set[Contract],
            ) -> T:
        """Requires a bump if there's a diff in functions."""

        # We first do a ``hash`` comparison, so it is still grosso modo.
        diff: Set[Contract] = files[0] ^ files[1] & files[0]
        total: int = len(diff)

        self.bar.info(f"Checking for {what} functions…\n")
        self.bar.init()

        for count, this in enumerate(diff):
            name: str
            that: Optional[Contract]
            checker: FuncChecker

            self.bar.push(count, total)

            # If it is not a functional change, we move on.
            if this is None or not self._is_functional(this.file):
                continue

            # We know we will fail already, but we still need to determine
            # the needed version bump.
            self.exit = Exit.KO

            # We will try to find a match between before/after contracts.
            name = this.name
            that = next((that for that in files[1] if that.name == name), None)

            # If we can't find a base contract with the same name, we can just
            # assume the function was added/removed, so minor/major.
            if that is None:
                bumper(what)
                self.bar.wipe()
                self.bar.warn(f"{str(bumper.what(what))} {name} => {what}\n")
                continue

            # Now we do a ``small-print`` comparison between contracts.
            f = FuncChecker(this, that)

            if f.score() == bumper.what(what).index:
                bumper(what)
                self.bar.wipe()
                self.bar.warn(f"{str(bumper.what(what))} {name} => {f.reason}")

        self.bar.wipe()

        return self

    def _check_version_acceptable(self: T, bumper: Bumper) -> T:
        """Requires a bump if there current version is not acceptable."""

        self.bar.info(f"Version bump required: {bumper.required.name}!\n")
        self.bar.okay(f"Current version: {bumper.this}")

        if bumper.is_acceptable():
            self.exit = Exit.OK
            return self

        self.bar.fail()

        return self

    def _is_functional(self, file: str) -> bool:
        """Checks if a given ``file`` is whitelisted as functional."""

        return not any(exclude in file for exclude in IGNORE)
