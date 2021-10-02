from __future__ import annotations

import pkg_resources
import subprocess
from typing import Any, NoReturn, Sequence, Type


class Files:
    """A descriptor to retrieve file change information.

    Attributes:
        repo: A generic service to run terminal commands.

    .. versionadded:: 36.1.0

    """

    repo: Repo

    def __get__(self, repo: Repo, repo_type: Type[Repo]) -> Files:
        self.repo = repo
        return self

    def __set__(self, repo: Repo, value: Any) -> NoReturn:
        raise NotImplementedError

    def show(self, file: str) -> str:
        """Retrives the content of a file in the last tagged version."""

        version: str = self.repo.versions.before()
        cmd: Sequence[str] = ["git", "show", f"{version}:{file}"]
        return self.repo.run(cmd)

    def actual(self) -> Sequence[str]:
        """Retrives the list of tracked files in the current revision."""

        cmd: Sequence[str] = ["git", "ls-tree", "-r", "--name-only", "HEAD"]
        res: Sequence[str] = self.repo.run(cmd).split()
        return [file for file in res if file.endswith(".py")]

    def before(self) -> Sequence[str]:
        """Retrives the list of tracked files in the last tagged version."""

        version: str = self.repo.versions.before()
        cmd: Sequence[str] = ["git", "ls-tree", "-r", "--name-only", version]
        res: Sequence[str] = self.repo.run(cmd).split()
        return [file for file in res if file.endswith(".py")]

    def changed(self) -> Sequence[str]:
        """Retrives the list of changed files since the last tagged version."""

        version: str = self.repo.versions.before()
        cmd: Sequence[str] = ["git", "diff-index", "--name-only", version]
        return self.repo.run(cmd).split()


class Versions:
    """A descriptor to retrieve version change information.

    Attributes:
        repo: A generic service to run terminal commands.

    .. versionadded:: 36.1.0

    """

    repo: Repo

    def __get__(self, repo: Repo, repo_type: Type[Repo]) -> Versions:
        self.repo = repo
        return self

    def __set__(self, repo: Repo, value: Any) -> NoReturn:
        raise NotImplementedError

    def actual(self) -> str:
        """Retrives the current version."""

        return pkg_resources.get_distribution("openfisca_core").version

    def before(self) -> str:
        """Retrives the last tagged version.

        Returns:
            The :obj:`str` representing the version.

        Examples:
            >>> repo = Repo()
            >>> version = repo.version.before()
            >>> major, minor, patch, *rest = version.split(".")
            >>> major.isdecimal()
            True

        .. versionadded:: 36.1.0

        """

        cmd: Sequence[str]
        cmd = ["git", "describe", "--tags", "--abbrev=0", "--first-parent"]
        return self.repo.run(cmd).split()[0]


class Repo:
    """A generic service to run terminal commands.

    Attributes:
        files: A descriptor to retrieve file change information.
        versions: A descriptor to retrieve version change information.

    .. versionadded:: 36.1.0

    """

    files: Files = Files()
    versions: Versions = Versions()

    @staticmethod
    def run(cmd: Sequence[str]) -> str:
        """Runs a command an decodes the result.

        Args:
            cmd: The command to run, as a list.

        Returns:
            The decoded ``stdout``.

        Examples:
            >>> Repo().run(["echo", "1"])
            '1\\n'

        .. versionadded:: 36.1.0

        """

        return \
            subprocess \
            .run(cmd, stdout = subprocess.PIPE) \
            .stdout \
            .decode("utf-8")
