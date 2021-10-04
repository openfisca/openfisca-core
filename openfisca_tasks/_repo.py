from __future__ import annotations

import pkg_resources
import subprocess
from typing import Sequence


class _File:
    """Retrieves file/change information.

    .. versionadded:: 36.1.0

    """

    @staticmethod
    def show(revision: str, file: str) -> str:
        """Retrives the content of a file in a revision.

        Args:
            revision: A commit, a tag, and so on…
            file: The relative file path.

        Returns:
            str: The contents of the file.

        Examples:
            >>> source = Repo.File.show("0.5.0", "openfisca_core/calmar.py")
            >>> source.split("\\n")[3]
            '# OpenFisca -- A versatile microsimulation software'

        """

        cmd: Sequence[str]
        cmd = ["git", "show", f"{revision}:{file}"]
        return Repo.run(cmd)

    @staticmethod
    def tree(revision: str) -> Sequence[str]:
        """Retrives the list of tracked files in a revision.

        Args:
            revision: A commit, a tag, and so on…

        Returns:
            A sequence with the files' names.

        Examples:
            >>> Repo.File.tree("0.5.0")[13]
            'openfisca_core/calmar.py'

        .. versionadded:: 36.1.0

        """

        cmd: Sequence[str]
        cmd = ["git", "ls-tree", "-r", "--name-only", revision]
        return Repo.run(cmd).split()

    @staticmethod
    def diff(this: str, that: str) -> Sequence[str]:
        """Retrives the list of changed files between two revisions.

        Args:
            this: A commit, a tag, and so on…
            that: The same as ``that``, but in the past…

        Returns:
            A sequence with the files' names.

        Examples:
            >>> Repo.File.diff("0.5.0", "0.5.1")
            ['.travis.yml', 'CHANGELOG.md', 'COPYING', 'Makefile', 'README.m...

        .. versionadded:: 36.1.0

        """

        cmd: Sequence[str]
        cmd = ["git", "diff", "--name-only", f"{that}..{this}"]
        return Repo.run(cmd).split()


class _Version:
    """Retrieves version/change information.

    .. versionadded:: 36.1.0

    """

    @staticmethod
    def this() -> str:
        """Retrives the actual version.

        Returns:
            str: Representing the version.

        Examples:
            >>> version = Repo.Version.this()
            >>> major, minor, patch, *rest = version.split(".")
            >>> major.isdecimal()
            True

        .. versionadded:: 36.1.0

        """

        return (
            pkg_resources
            .get_distribution("openfisca_core")
            .version
            )

    @staticmethod
    def last() -> str:
        """Retrives the last tagged version.

        Returns:
            str: Representing the version.

        Examples:
            >>> version = Repo.Version.last()
            >>> major, minor, patch, *rest = version.split(".")
            >>> major.isdecimal()
            True

        .. versionadded:: 36.1.0

        """

        cmd: Sequence[str]
        cmd = ["git", "describe", "--tags", "--abbrev=0", "--first-parent"]
        return Repo.run(cmd).split()[0]


class Repo:
    """A generic service to run terminal commands.

    Attributes:
        files: A descriptor to retrieve file change information.
        versions: A descriptor to retrieve version change information.

    .. versionadded:: 36.1.0

    """

    File = _File
    Version = _Version

    @staticmethod
    def run(cmd: Sequence[str]) -> str:
        """Runs a command an decodes the result.

        Args:
            cmd: The command to run, as a list.

        Returns:
            The decoded ``stdout``.

        Examples:
            >>> Repo.run(["echo", "1"])
            '1\\n'

        .. versionadded:: 36.1.0

        """

        return \
            subprocess \
            .run(cmd, check = True, stdout = subprocess.PIPE) \
            .stdout \
            .decode("utf-8")
