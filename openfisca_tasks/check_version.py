from __future__ import annotations

from typing import Optional, Sequence, Set, TypeVar

from openfisca_core.indexed_enums import Enum

from openfisca_tasks import SupportsProgress

from ._builder import Contract
from ._bumper import Bumper
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
        exit: An exit code.
        progress: A progress bar.
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

            self.bar.push(count, total)

            # If it is not a functional change, we move on.
            if this is None or not self._is_functional(this.file):
                continue

            # We know we will fail already, but we still need to determine
            # the needed version bump.
            self.exit = Exit.KO

            # Now we do a ``small-print`` comparison between contracts.
            # First, trying to find a corresponding contract before/after.
            name = this.name
            that = next((that for that in files[1] if that.name == name), None)

            # If we can't find a base contract with the same name, we can just
            # assume the function was added/removed, so minor/major.
            if that is None:
                bumper(what)
                self.bar.wipe()
                self.bar.warn(f"{str(bumper.what(what))} {name} => {what}\n")
                continue

            # If arguments were removed we can safely assume a breaking change,
            # but not so when we add them, as they can be default arguments.
            if this.arguments is None and that.arguments is not None:
                message = [
                    f"{name} =>",
                    f"Argument mismatch: 0 != {len(that.arguments)}\n",
                    ]

                if not all(argument.default for argument in that.arguments):
                    message = [f"{str(bumper.what('removed'))}", *message]
                    bumper("removed")
                    self.bar.wipe()
                    self.bar.warn(" ".join(message))
                    continue

                else:
                    message = [f"{str(bumper.what('added'))}", *message]
                    bumper("added")
                    self.bar.wipe()
                    self.bar.warn(" ".join(message))

            # If both functions' arguments are equal, we can assume a patch
            # bump as that means a diff in the return types, which are just
            # annotations.
            if this.arguments == that.arguments:
                continue

            # We move on as we'll catch this scenario in a second round.
            if this.arguments is not None and that.arguments is None:
                continue

            # Finally, we need to cast this for the type-checker.
            if this.arguments is None or that.arguments is None:
                continue

            if len(this.arguments) == len(that.arguments):

                for count, thisarg in enumerate(this.arguments):
                    thatarg = that.arguments[count]

                    # If there's an argument name mismatch, we can assume a
                    # major bump is needed.
                    if thisarg.name != thatarg.name:

                        message = [
                            f"{str(bumper.what('removed'))} {name} =>",
                            f"{thisarg.name} != {thatarg.name}\n",
                            ]

                        bumper("removed")
                        self.bar.wipe()
                        self.bar.warn(" ".join(message))
                        continue

                    # Also if there's a change in default arguments, either
                    # a minor or a major bump is needed.
                    if thisarg.default is not None and thatarg.default is None:

                        message = [
                            f"{str(bumper.what(what))} {name} =>",
                            f"{thisarg.name} (= {thisarg.default}) !=",
                            f"{thatarg.name} (= {thatarg.default})\n",
                            ]

                        bumper(what)
                        self.bar.wipe()
                        self.bar.warn(" ".join(message))

            # Finally we take a look at the remaining diff in arguments.
            thisnames = set(argument.name for argument in this.arguments)
            thatnames = set(argument.name for argument in that.arguments)

            namesdiff = thisnames ^ thatnames & thisnames

            for thatname in namesdiff:
                message = [
                    f"{str(bumper.what(what))} {name} =>",
                    f"{thatname}!\n",
                    ]

                bumper(what)
                self.bar.wipe()
                self.bar.warn(" ".join(message))

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
