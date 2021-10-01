import subprocess
from typing import Sequence

from typing_extensions import Literal

from ._protocols import SupportsProgress

EXIT_OK: Literal[0]
EXIT_OK = 0

EXIT_KO: Literal[1]
EXIT_KO = 1

IGNORE_DIFF_ON: Sequence[str]
IGNORE_DIFF_ON = (
    ".circleci/*",
    ".github/*",
    "openfisca_tasks/*",
    "tests/*",
    ".gitignore"
    "conftest.py",
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

class CheckVersion:

    exit: Literal[0, 1]

    def __init__(self):
        self.exit = EXIT_OK

    def __call__(self, progress: SupportsProgress) -> None:
        self.progress = progress

        if self._haschanges():
            self.exit = EXIT_KO

    def _haschanges(self) -> bool:
        changed: bool
        changed = False

        for file in CHANGED:
            if file not in IGNORE_DIFF_ON:
                self.progress.warn(f"{file}\n")
                changed = True

        return changed
