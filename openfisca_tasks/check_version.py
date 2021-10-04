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

    def check_signs(self):
        sys.stdout.write("[i] Analizing signature changes…\n")
        self.__init_progress__()
        self.buffer = []

        for count, contract in enumerate(self.after):
            self.__push_progress__(self.after, count)

            baseline = next((
                baseline
                for baseline in self.avant
                if baseline.func == contract.func
                ), None)

            if baseline is None:
                continue

            avant = set(baseline.inputs)
            after = set(contract.inputs)

            if len(avant) == len(after):
                for index, argument in enumerate(contract.inputs):
                    base_arg = baseline.inputs[index]

                    if argument != base_arg:

                        diff_avant = [
                            f"name = {base_arg.name}\n",
                            f"type = {[base_arg.type_, ''][base_arg.type_ is None]}\n",
                            f"default = {[base_arg.default, ''][base_arg.default is None]}\n",
                            ]

                        diff_apres = [
                            f"name = {argument.name}\n",
                            f"type = {[argument.type_, ''][argument.type_ is None]}\n",
                            f"default = {[argument.default, ''][argument.default is None]}\n",
                            ]

                        self.buffer += [[diff_avant, diff_apres, contract.func]]

                        self.__wipe_progress__()

                        if argument.name != base_arg:
                            sys.stdout.write(f"[~] Argument => {contract.func} (requires a major release)\n")

                        elif argument.default is None and base_arg.default is not None:
                            sys.stdout.write(f"[~] Argument => {contract.func} (requires a major release)\n")

                        else:
                            sys.stdout.write(f"[~] Argument => {contract.func} (requires a patch release)\n")

            if len(avant) != len(after):

                added = (after ^ avant & after)

                for argument in added:
                    diff_apres = [
                        f"name = {argument.name}\n",
                        f"type = {[argument.type_, ''][argument.type_ is None]}\n",
                        f"default = {[argument.default, ''][argument.default is None]}\n",
                        ]

                    self.buffer += [[["\n"], diff_apres, contract.func]]

                    self.__wipe_progress__()

                    sys.stdout.write(f"[+] Argument => {contract.func} (requires a minor release)\n")

                removed = (avant ^ after & avant)

                for argument in removed:
                    diff_avant = [
                        f"name = {argument.name}\n",
                        f"type = {[argument.type_, ''][argument.type_ is None]}\n",
                        f"default = {[argument.default, ''][argument.default is None]}\n",
                        ]

                    self.buffer += [[diff_avant, ["\n"], contract.func]]

                    self.__wipe_progress__()
                    sys.stdout.write(f"[-] Argument => {contract.func} (requires a major release)\n")

            if contract.output != baseline.output:

                if baseline.output is None:
                    if isinstance(contract.output, Type):
                        diff_apres = [f"{contract.output}\n"]

                    if isinstance(contract.output, tuple):
                        diff_apres = [f"{contract.output}\n"]

                    self.buffer += [[["\n"], diff_apres, contract.func]]

                    self.__wipe_progress__()
                    sys.stdout.write(f"[+] Returntp => {contract.func} (requires a patch release)\n")

                if contract.output is None:
                    if isinstance(baseline.output, Type):
                        diff_avant = [f"{baseline.output}\n"]

                    if isinstance(baseline.output, tuple):
                        diff_avant = [f"{baseline.output}\n"]

                    self.buffer += [[diff_avant, ["\n"], contract.func]]

                    self.__wipe_progress__()
                    sys.stdout.write(f"[-] Returntp => {contract.func} (requires a patch release)\n")

        self.__wipe_progress__()

        for diff_avant, diff_apres, func in self.buffer:
            sys.stdout.write("\n")
            sys.stdout.writelines(
                difflib.unified_diff(
                    diff_avant,
                    diff_apres,
                    fromfile = func,
                    tofile = func,
                    )
                )

        self.__wipe_progress__()


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
