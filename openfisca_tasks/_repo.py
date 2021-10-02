from __future__ import annotations

import pkg_resources
import subprocess
from typing import Sequence


class Repo:

    @property
    def version(self) -> Repo:
        return self

    def current(self) -> str:
        return \
            pkg_resources \
            .get_distribution("openfisca_core") \
            .version

    def tagged(self) -> str:
        return self._run(self._describe()).split()[0]

    @property
    def files(self) -> Repo:
        return self

    def show(self, file: str) -> str:
        return self._run(self._show(file))

    def changed(self) -> Sequence[str]:
        return self._run(self._diff_index()).split()

    def actual(self) -> Sequence[str]:
        return [
            file
            for file in self._run(self._ls_tree("HEAD")).split()
            if file.endswith(".py")
            ]

    def before(self) -> Sequence[str]:
        return [
            file
            for file in self._run(self._ls_tree(self.version.tagged())).split()
            if file.endswith(".py")
            ]

    @staticmethod
    def _run(cmd: Sequence[str]) -> str:
        return \
            subprocess \
            .run(cmd, stdout = subprocess.PIPE) \
            .stdout \
            .decode("utf-8")

    @staticmethod
    def _describe() -> Sequence[str]:
        return ["git", "describe", "--tags", "--abbrev=0", "--first-parent"]

    def _diff_index(self) -> Sequence[str]:
        return ["git", "diff-index", "--name-only", self.version.tagged()]

    @staticmethod
    def _ls_tree(revision: str) -> Sequence[str]:
        return ["git", "ls-tree", "-r", "--name-only", revision]

    @staticmethod
    def _show(file: str) -> Sequence[str]:
        return ["git", "show", f"master:{file}"]
