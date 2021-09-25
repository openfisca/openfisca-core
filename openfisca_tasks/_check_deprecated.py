import ast
import os
import pathlib
import pkg_resources
import subprocess
import sys
import textwrap
from typing import Sequence

FILES: Sequence[str]
FILES = \
    subprocess \
    .run(["git", "ls-files", "*.py"], stdout = subprocess.PIPE) \
    .stdout \
    .decode("utf-8") \
    .split()

VERSION: str
VERSION = \
    pkg_resources \
    .get_distribution("openfisca_core") \
    .version


class CheckDeprecated(ast.NodeVisitor):

    count: int
    exit: int = os.EX_OK
    files: Sequence[str]
    nodes: Sequence[ast.Module]
    version: str

    def __init__(
            self,
            files: Sequence[str] = FILES,
            version: str = VERSION,
            ) -> None:

        self.files = files
        self.nodes = [self._node(file) for file in self.files]
        self.version = version

    def __call__(self) -> None:
        for count, node in enumerate(self.nodes):
            self.count = count
            self.visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        keywords: Sequence[str]
        file: str
        path: pathlib.Path
        module: str
        lineno: int
        since: str
        expires: str
        message: Sequence[str]

        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                break

            if "deprecated" in ast.dump(decorator):
                keywords = [
                    kwd.value.s
                    for kwd in decorator.keywords
                    if isinstance(kwd.value, ast.Str)
                    ]

                file = self.files[self.count]
                path = pathlib.Path(file).resolve()
                module = f"{path.parts[-2]}.{path.stem}"
                lineno = node.lineno + 1
                since, expires = keywords

                if self._isthis(expires):
                    self.exit = 1

                message = [
                    f"[{module}.{node.name}:{lineno}]",
                    f"Deprecated since: {since}.",
                    f"Expiration status: {expires}",
                    f"(current: {self.version}).",
                    ]

                sys.stdout.write(f"{' '.join(message)}\n")

    def _isthis(self, version: str) -> bool:
        return self.version == version

    def _node(self, file: str) -> ast.Module:
        source: str

        with open(file, "r") as f:
            source = textwrap.dedent(f.read())
            return ast.parse(source, file, "exec")
