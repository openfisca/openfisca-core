import pkg_resources
import subprocess
from typing import Sequence


def changed_files() -> Sequence[str]:
    return _run(_diff_index())


def before_version() -> str:
    return _run(_describe())[0]


def before_files() -> Sequence[str]:
    return [
        file
        for file in _run(_ls_tree(before_version()))
        if file.endswith(".py")
        ]


def actual_version() -> str:
    return \
        pkg_resources \
        .get_distribution("openfisca_core") \
        .version


def actual_files() -> Sequence[str]:
    return [
        file
        for file in _run(_ls_tree("HEAD"))
        if file.endswith(".py")
        ]


def _run(cmd: Sequence[str]) -> Sequence[str]:
    return \
        subprocess \
        .run(cmd, stdout = subprocess.PIPE) \
        .stdout \
        .decode("utf-8") \
        .split()


def _describe() -> Sequence[str]:
    return ["git", "describe", "--tags", "--abbrev=0", "--first-parent"]


def _diff_index() -> Sequence[str]:
    return ["git", "diff-index", "--name-only", before_version()]


def _ls_tree(revision: str) -> Sequence[str]:
    return ["git", "ls-tree", "-r", "--name-only", revision]
