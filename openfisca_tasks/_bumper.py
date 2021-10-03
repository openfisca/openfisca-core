from typing import Type, Union

from openfisca_core.indexed_enums import Enum

from ._repo import Repo

TO_STR = "-", "+", "~", ""


class Version(Enum):
    MAJOR = "removed"
    MINOR = "added"
    PATCH = "diff"
    NONE = "none"

    def __str__(self) -> str:
        return TO_STR[self.index]


class Bumper:

    repo: Repo
    what: Type[Version]
    before: str
    actual: str
    required: Version

    def __init__(self) -> None:
        self.repo = Repo()
        self.what = Version
        self.before = self.repo.versions.before()
        self.actual = self.repo.versions.actual()
        self.required = Version.NONE

    def __call__(self, bump: str) -> None:
        index = min(self.required.index, Version(bump).index)
        self.required = tuple(Version)[index]

    def is_acceptable(self) -> bool:
        actual: int = int(self.actual.split(".")[self.required.index])
        before: int = int(self.before.split(".")[self.required.index])
        return actual >= before + 1
