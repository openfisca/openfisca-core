import re
from typing import Sequence, Tuple, Type

from openfisca_core.indexed_enums import Enum

from ._repo import Repo

TO_STR = "-", "+", "~", ""


class Version(Enum):
    """An enum just to determine the required version.

    Examples:
        >>> [str(version) for version in Version]
        ['-', '+', '~', '']

        >>> [version.name for version in Version]
        ['MAJOR', 'MINOR', 'PATCH', 'NONE']

        >>> [version.value for version in Version]
        ['removed', 'added', 'diff', 'none']

        >>> [version.index for version in Version]
        [0, 1, 2, 3]

    """

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

        >>> bumper.required
        <Version.NONE: 'none'>

        >>> bumper.what("removed")
        <Version.MAJOR: 'removed'>

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
            >>> bumper.is_acceptable()
            True

            >>> bumper("removed")
            >>> bumper.actual = "1.2.3"
            >>> bumper.before = "1.2.3"
            >>> bumper.is_acceptable()
            False

            >>> bumper.actual = "2.0.0"
            >>> bumper.is_acceptable()
            True

            >>> bumper.actual = "2.0.0-rc.1+1234"
            >>> bumper.is_acceptable()
            True

            >>> bumper.before = "2.0.0-asdf+1234"
            >>> bumper.is_acceptable()
            True

        .. versionadded:: 36.1.0

        """

        actual_number: int
        actual_is_rel: bool
        before_number: int
        before_is_rel: bool

        # If there's no required bump, we just do not check.
        if self.required == Version.NONE:
            return True

        # We get the actual number and whether it is a release or not.
        actual_number, actual_is_rel = self._extract(self.actual)

        # We get the last tagged number and whether it is a release or not.
        before_number, before_is_rel = self._extract(self.before)

        # If both are releases, next version has to be major/minor/patch +1.
        if actual_is_rel and before_is_rel:
            before_number += 1

        # Otherwise we just do not check.
        # It is way too anecdotic for the complexity that check requires.
        return actual_number >= before_number

    def _extract(self, version: str) -> Tuple[int, bool]:
        """Extract a major/minor/patch number from a version string."""

        is_release: bool
        release: str
        rest: Sequence[str]

        # We separate the non-release par, ex: ``-pre+1``.
        release, *rest = re.split("\\+|\\-", version)

        # We get the major/minor/patch number based on the required bump.
        number: str = release.split(".")[self.required.index]

        # Finally we determine if this is a release or not.
        is_release = len(rest) == 0

        return int(number), is_release
