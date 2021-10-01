from __future__ import annotations

import ast
import textwrap
import subprocess
from typing import Generator, Sequence

from typing_extensions import Literal

from ._protocols import SupportsProgress

from openfisca_core.indexed_enums import Enum

EXIT_OK: Literal[0]
EXIT_OK = 0

EXIT_KO: Literal[1]
EXIT_KO = 1

IGNORE_DIFF_ON: Sequence[str]
IGNORE_DIFF_ON = (
    ".circleci/*",
    ".github/*",
    "tests/*",
    ".gitignore"
    "CONTRIBUTING.md",
    "LICENSE*",
    "Makefile",
    "README.md",
    "STYLEGUIDE.md",
    )

VERSION: str
VERSION = \
    subprocess \
    .run(
        ["git", "describe", "--tags", "--abbrev=0", "--first-parent"],
        stdout = subprocess.PIPE,
        ) \
    .stdout \
    .decode("utf-8") \
    .split()[0]

CHANGED: Sequence[str]
CHANGED = \
    subprocess \
    .run(
        ["git", "diff-index", "--name-only", VERSION],
        stdout = subprocess.PIPE,
        ) \
    .stdout \
    .decode("utf-8") \
    .split()

ACTUAL: Sequence[str]
ACTUAL = [
    file
    for file in
    subprocess
    .run(
        ["git", "ls-tree", "-r", "HEAD", "--name-only"],
        stdout = subprocess.PIPE,
        )
    .stdout
    .decode("utf-8")
    .split()
    if file.endswith(".py")
    ]

BEFORE: Sequence[str]
BEFORE = [
    file
    for file in
    subprocess
    .run(
        ["git", "ls-tree", "-r", VERSION, "--name-only"],
        stdout = subprocess.PIPE,
        )
    .stdout
    .decode("utf-8")
    .split()
    if file.endswith(".py")
    ]


class Version(Enum):
    NONE = "none"
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"


class CheckVersion:

    exit: Literal[0, 1]
    version: int

    def __init__(self):
        self.exit = EXIT_OK
        self.version = Version.NONE.index

    def __call__(self, progress: SupportsProgress) -> None:
        required: str

        self.progress = progress
        self.actual = tuple(self._parse_actual())
        self.before = tuple(self._parse_before())

        if self._haschanges():
            self.exit = EXIT_KO

        required = tuple(Version)[self.version].value
        self.progress.info(f"Version bump required: {required}!\n")

    def _haschanges(self) -> bool:
        total: int
        total = len(CHANGED)

        self.progress.info("Checking for functional changes…\n")
        self.progress.init()

        for count, file in enumerate(CHANGED):
            if file not in IGNORE_DIFF_ON:
                self.version = max(self.version, Version.PATCH.index)
                self.progress.wipe()
                self.progress.warn(f"{file}\n")

            self.progress.push(count, total)

        self.progress.wipe()
        return bool(self.version)

    def _parse_actual(self) -> Generator[ast.Module, None, None]:
        source: str
        total: int

        total = len(ACTUAL)

        self.progress.info("Parsing files from the current branch…\n")
        self.progress.init()

        for count, filename in enumerate(ACTUAL):
            with open(filename, "r") as file:
                source = textwrap.dedent(file.read())
                yield ast.parse(source, filename, "exec")
                self.progress.push(count, total)

        self.progress.wipe()

    def _parse_before(self) -> Generator[ast.Module, None, None]:
        content: str
        source: str
        total: int

        total = len(BEFORE)

        self.progress.info(f"Parsing files from version {VERSION}…\n")
        self.progress.init()

        for count, filename in enumerate(BEFORE):
            content = \
                subprocess \
                .run(
                    ["git", "show", f"master:{filename}"],
                    stdout = subprocess.PIPE) \
                .stdout \
                .decode("utf-8")

            source = textwrap.dedent(content)
            yield ast.parse(source, filename, "exec")
            self.progress.push(count, total)

        self.progress.wipe()
