from typing import Type

from openfisca_core.indexed_enums import Enum

from ._repo import Repo

TO_STR = "-", "+", "~", ""


class Version(Enum):
    """An enum just to determine the required version."""

    MAJOR = "removed"
    MINOR = "added"
    PATCH = "diff"
    NONE = "none"

    def __str__(self) -> str:
        return TO_STR[self.index]


class Bumper:
    """Determines the required version bump.

    Attributes:
        repo: To gather versions.
        what: An ``event`` and the associated bump requirement.
        before: The last tagged version.
        actual: The actual version.
        required: The required version bump.

    Examples:
        >>> bumper = Bumper()
        >>> bumper("removed")
        >>> bumper.required
        <Version.MAJOR: 'removed'>

    .. versionadded:: 36.1.0

    """

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
        """Determines if the current version is acceptable or not.

        Returns:
            True: When it is acceptable.
            False: Otherwise.

        Examples:
            >>> bumper = Bumper()
            >>> bumper("removed")

            >>> bumper.actual = "1.2.3"
            >>> bumper.before = "1.2.3"
            >>> bumper.is_acceptable()
            False

            >>> bumper.actual = "2.0.0"
            >>> bumper.is_acceptable()
            True

        .. versionadded:: 36.1.0

        """

        actual: int = int(self.actual.split(".")[self.required.index])
        before: int = int(self.before.split(".")[self.required.index])
        return actual >= before + 1
