from __future__ import annotations

import ast
import dataclasses
import functools
import pathlib
import textwrap
import subprocess
from typing import Generator, Optional, Sequence

from typing_extensions import Literal

from . import _repo, SupportsProgress

from openfisca_core.indexed_enums import Enum

EXIT_OK: Literal[0]
EXIT_OK = 0

EXIT_KO: Literal[1]
EXIT_KO = 1

IGNORE_DIFF_ON: Sequence[str]
IGNORE_DIFF_ON = (
    ".circleci",
    ".github",
    ".gitignore",
    ".mk",
    "CONTRIBUTING.md",
    "LICENSE",
    "Makefile",
    "README.md",
    "STYLEGUIDE.md",
    "tests",
    )

BEFORE_VERSION: str
BEFORE_VERSION = _repo.before_version()

ACTUAL_VERSION: str
ACTUAL_VERSION = _repo.actual_version()

BEFORE_FILES: Sequence[str]
BEFORE = _repo.before_files()

ACTUAL_FILES: Sequence[str]
ACTUAL = _repo.actual_files()

CHANGED: Sequence[str]
CHANGED = _repo.changed_files()


class Version(Enum):
    NONE = "none"
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"


@dataclasses.dataclass(frozen = True)
class Type:
    name: str


@dataclasses.dataclass(frozen = True)
class RType:
    name: str


@dataclasses.dataclass(frozen = True)
class Argument:
    name: str
    type_: Optional[Type] = None
    default: Optional[str] = None


@dataclasses.dataclass(frozen = True)
class Contract:
    name: str
    file: str
    arguments: Optional[Sequence[Argument]] = None
    returns: Optional[Sequence[RType]] = None


class CheckVersion(ast.NodeVisitor):

    actual: Sequence[Contract]
    before: Sequence[Contract]
    changed: Sequence[str]
    contracts: Sequence[Contract]
    exit: Literal[0, 1]
    files: Sequence[str]
    progress: SupportsProgress
    required: int
    version: str

    def __init__(
            self,
            changed: Sequence[str] = CHANGED,
            version: str = ACTUAL_VERSION,
            ):
        self.exit = EXIT_OK
        self.changed = changed
        self.version = Version.NONE.index

    def __call__(self, progress: SupportsProgress) -> None:
        self.progress = progress
        self.actual = tuple(
            nodes
            for node in self._parse_actual()
            for nodes in node
            )
        self.before = tuple(
            nodes
            for node in self._parse_before()
            for nodes in node
            )

        if self._haschanges():
            self.exit = EXIT_KO

        if self._hasaddedfuncs():
            self.exit = EXIT_KO

        if self._hasdelfuncs():
            self.exit = EXIT_KO

        required = tuple(Version)[self.version].value
        self.progress.info(f"Version bump required: {required}!\n")
        self.progress.okay(f"Current version: {ACTUAL_VERSION}")

        if int(ACTUAL_VERSION.split(".")[::-1][self.version - 1]) >= int(BEFORE_VERSION.split(".")[::-1][self.version - 1]) + 1:
            self.exit = EXIT_OK

        if self.exit == EXIT_KO:
            self.progress.fail()

        self.progress.next()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # We look for the corresponding ``file``.
        file = self.files[self.count]

        # We find the absolute path of the file.
        path = pathlib.Path(file).resolve()

        # We build the module name with the name of the parent path, a
        # folder, and the name of the file, without the extension.
        module = f"{path.parts[-2]}.{path.stem}"

        name = node.name

        if name.startswith("_") and not name.endswith("_"):
            return

        if name.startswith("__") and name not in ("__init__", "__call__"):
            return

        name = f"{module}.{node.name}"

        for decorator in node.decorator_list:
            if "property" in ast.dump(decorator):
                name = f"{name}#getter"

            if "setter" in ast.dump(decorator):
                name = f"{name}#setter"

        build = functools.partial(
            self._build_argument,
            args = node.args.args,
            defaults = node.args.defaults,
            )

        posargs = functools.reduce(build, node.args.args, ())

        build = functools.partial(
            self._build_argument,
            args = node.args.kwonlyargs,
            defaults = node.args.kw_defaults,
            )

        keyargs = functools.reduce(build, node.args.kwonlyargs, ())

        self.contracts.append(Contract(name, file, posargs + keyargs))

    def _haschanges(self) -> bool:
        total: int
        total = len(self.changed)

        self.progress.info("Checking for functional changes…\n")
        self.progress.init()

        for count, file in enumerate(self.changed):
            if not self._isfunctional(file):
                continue

            self.version = max(self.version, Version.PATCH.index)
            self.progress.wipe()
            self.progress.warn(f"~ {file}\n")

            self.progress.push(count, total)

        self.progress.wipe()
        return bool(self.version)

    def _hasaddedfuncs(self) -> bool:
        actual = set(contract.name for contract in self.actual)
        before = set(contract.name for contract in self.before)

        added = actual ^ before & actual
        total = len(added)

        self.progress.info("Checking for added functions…\n")
        self.progress.init()

        for count, name in enumerate(added):
            contract = self._find(name, self.actual)

            if contract is None or not self._isfunctional(contract.file):
                continue

            self.version = max(self.version, Version.MINOR.index)
            self.progress.wipe()
            self.progress.warn(f"+ {contract.name}\n")
            self.progress.push(count, total)

        self.progress.wipe()
        return bool(self.version)

    def _hasdelfuncs(self) -> bool:
        actual = set(contract.name for contract in self.actual)
        before = set(contract.name for contract in self.before)

        removed = (before ^ actual & before)
        total = len(removed)

        self.progress.info("Checking for removed functions…\n")
        self.progress.init()

        for count, name in enumerate(removed):
            contract = self._find(name, self.before)

            if contract is None or not self._isfunctional(contract.file):
                continue

            self.version = max(self.version, Version.MAJOR.index)
            self.progress.wipe()
            self.progress.warn(f"- {contract.name}\n")
            self.progress.push(count, total)

        self.progress.wipe()
        return bool(self.version)

    def _isfunctional(self, file: str) -> bool:
        return not any(exclude in file for exclude in IGNORE_DIFF_ON)

    def _find(self, name: str, pool: Sequence[Contract]) -> Optional[Contract]:
        return next(
            (
                contract
                for contract in pool
                if contract.name == name
                ),
            None,
            )

    def _parse_actual(self) -> Generator[ast.Module, None, None]:
        source: str
        total: int

        self.files = ACTUAL
        total = len(self.files)

        self.progress.info("Parsing files from the current branch…\n")
        self.progress.init()

        for count, filename in enumerate(self.files):
            self.contracts = []
            self.count = count

            with open(filename, "r") as file:
                source = textwrap.dedent(file.read())
                node = ast.parse(source, filename, "exec")
                self.visit(node)
                yield self.contracts
                self.progress.push(count, total)

        self.progress.wipe()

    def _parse_before(self) -> Generator[ast.Module, None, None]:
        self.contracts = []
        content: str
        source: str
        total: int

        self.files = BEFORE
        total = len(self.files)

        self.progress.info(f"Parsing files from version {BEFORE_VERSION}…\n")
        self.progress.init()

        for count, filename in enumerate(self.files):
            self.count = count

            content = \
                subprocess \
                .run(
                    ["git", "show", f"master:{filename}"],
                    stdout = subprocess.PIPE) \
                .stdout \
                .decode("utf-8")

            source = textwrap.dedent(content)
            node = ast.parse(source, filename, "exec")
            self.visit(node)
            yield self.contracts
            self.progress.push(count, total)

        self.progress.wipe()

    def _build_argument(self, acc, node, args, defaults) -> Sequence[Argument]:
        type_ = self._build(node.annotation, Type)

        if type_ is not None and not isinstance(type_, tuple):
            type_ = type_,

        if len(defaults) > 0 and len(args) - len(defaults) < len(acc) + 1:
            default = defaults[
                + len(acc)
                + len(defaults)
                - len(args)
                ]

            default = self._build(default)
        else:
            default = None

        argument = Argument(node.arg, type_, default)

        return (*acc, argument)

    def _build(self, node, builder = lambda x: x):
        if node is None:
            return None

        if isinstance(node, ast.Attribute):
            return builder(str(node.attr))

        if isinstance(node, ast.Name):
            return builder(str(node.id))

        if isinstance(node, (ast.Constant, ast.NameConstant)):
            return builder(str(node.value))

        if isinstance(node, ast.Num):
            return builder(str(node.n))

        if isinstance(node, ast.Str):
            return builder(str(node.s))

        if isinstance(node, ast.Subscript):
            return (
                self._build(node.value, builder),
                self._build(node.slice.value, builder),
                )

        if isinstance(node, ast.Tuple):
            return functools.reduce(
                lambda acc, item: (*acc, self._build(item, builder)),
                node.elts,
                (),
                )

        raise TypeError(ast.dump(node))
