from __future__ import annotations

import pkg_resources
import subprocess
from typing import Any, NoReturn, Sequence, Type


class Files:

    repo: Repo

    def __get__(self, repo: Repo, repo_type: Type[Repo]) -> Files:
        self.repo = repo
        return self

    def __set__(self, repo: Repo, value: Any) -> NoReturn:
        raise NotImplementedError

    def show(self, file: str) -> str:
        version: str = self.repo.version.before()
        cmd: Sequence[str] = ["git", "show", f"{version}:{file}"]
        return self.repo.run(cmd)

    def actual(self) -> Sequence[str]:
        cmd: Sequence[str] = ["git", "ls-tree", "-r", "--name-only", "HEAD"]
        res: Sequence[str] = self.repo.run(cmd).split()
        return [file for file in res if file.endswith(".py")]

    def before(self) -> Sequence[str]:
        version: str = self.repo.version.before()
        cmd: Sequence[str] = ["git", "ls-tree", "-r", "--name-only", version]
        res: Sequence[str] = self.repo.run(cmd).split()
        return [file for file in res if file.endswith(".py")]

    def changed(self) -> Sequence[str]:
        version: str = self.repo.version.before()
        cmd: Sequence[str] = ["git", "diff-index", "--name-only", version]
        return self.repo.run(cmd).split()


class Version:

    repo: Repo

    def __get__(self, repo: Repo, repo_type: Type[Repo]) -> Version:
        self.repo = repo
        return self

    def __set__(self, repo: Repo, value: Any) -> NoReturn:
        raise NotImplementedError

    def actual(self) -> str:
        return pkg_resources.get_distribution("openfisca_core").version

    def before(self) -> str:
        cmd: Sequence[str]
        cmd = ["git", "describe", "--tags", "--abbrev=0", "--first-parent"]
        return self.repo.run(cmd).split()[0]


class Repo:

    files = Files()
    version = Version()

    @staticmethod
    def run(cmd: Sequence[str]) -> str:
        return \
            subprocess \
            .run(cmd, stdout = subprocess.PIPE) \
            .stdout \
            .decode("utf-8")
