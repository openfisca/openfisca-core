from __future__ import annotations

import ast
import dataclasses
import functools
import pathlib
from typing import Any, Callable, Optional, Sequence, Tuple


@dataclasses.dataclass(frozen = True)
class ArgType:
    name: str


@dataclasses.dataclass(frozen = True)
class RetType:
    name: str


@dataclasses.dataclass(frozen = True)
class Argument:
    name: str
    types: Optional[Tuple[ArgType, ...]] = None
    default: Optional[str] = None


@dataclasses.dataclass(frozen = True)
class Contract:
    name: str
    file: str
    arguments: Optional[Sequence[Argument]] = None
    returns: Optional[Sequence[RetType]] = None


@dataclasses.dataclass
class ContractBuilder(ast.NodeVisitor):
    """
    Examples:
        >>> ContractBuilder(["file.py"])
        ContractBuilder(files=['file.py'], count=0, contracts=())

    """

    files: Sequence[str]
    count: int = 0
    contracts: Tuple[Contract, ...] = ()

    @property
    def total(self) -> int:
        """
        Examples:
            >>> builder = ContractBuilder(["file.py"])
            >>> builder.total
            1

        """

        return len(self.files)

    def __call__(self, source: str) -> None:
        """
        Examples:
            >>> builder = ContractBuilder(["file.py"])
            >>> source = [
            ...     "def function(n: List[int] = [1]) -> int:",
            ...     "    return next(iter(n))",
            ...     ]
            >>> builder("\\n".join(source))
            >>> contract = next(iter(builder.contracts))
            >>> argument = next(iter(contract.arguments))

            >>> builder.contracts
            (Contract(name='openfisca-core.file.function', file='file.py', a...

            >>> contract.name
            'openfisca-core.file.function'

            >>> contract.file
            'file.py'

            >>> contract.arguments
            (Argument(name='n', types=(ArgType(name='List'), ArgType(name='i...

            >>> argument.name
            'n'

            >>> argument.types
            (ArgType(name='List'), ArgType(name='int'))

            >>> argument.default
            ('1',)

            >>> contract.returns
            (RetType(name='int'),)

            >>> builder.count
            1

        """

        node = ast.parse(source, self.files[self.count], "exec")
        self.visit(node)
        self.count += 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        contract: Contract

        # We look for the corresponding ``file``.
        file = self.files[self.count]

        # We find the absolute path of the file.
        path = pathlib.Path(file).resolve()

        # We build the module name with the name of the parent path, a
        # folder, and the name of the file, without the extension.
        module = f"{path.parts[-2]}.{path.stem}"

        # We take de node name as a base.
        name = node.name

        # We pass if its a private function.
        if name.startswith("_") and not name.endswith("_"):
            return

        # We pass if it is a special function not in __init__ or __call__.
        if name.startswith("__") and name not in ("__init__", "__call__"):
            return

        # We compose the name with the name of the module.
        name = f"{module}.{node.name}"

        # We suffix properties, othersise names would duplicate.
        for decorator in node.decorator_list:
            if "property" in ast.dump(decorator):
                name = f"{name}#getter"

            if "setter" in ast.dump(decorator):
                name = f"{name}#setter"

        # We build all positional arguments.
        posargs = functools.reduce(
            self._build_posarg(node),
            node.args.args,
            (),
            )

        # We build all keyword arguments.
        keyargs = functools.reduce(
            self._build_keyarg(node),
            node.args.kwonlyargs,
            (),
            )

        # We build the return types.
        returns = self._build_returns(node)

        # We build the contract.
        contract = Contract(name, file, posargs + keyargs, returns)

        # And we add it to the list of contracts.
        self.contracts = self.contracts + (contract,)

    def _build_posarg(self, node: ast.FunctionDef) -> Callable[..., Any]:
        return functools.partial(
            self._build_argument,
            args = node.args.args,
            defaults = node.args.defaults,
            )

    def _build_keyarg(self, node: ast.FunctionDef) -> Callable[..., Any]:
        return functools.partial(
            self._build_argument,
            args = node.args.kwonlyargs,
            defaults = node.args.kw_defaults,
            )

    def _build_argument(self, acc, node, args, defaults) -> Sequence[Argument]:
        type_ = self._build(node.annotation, ArgType)

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

    def _build_returns(self, node: ast.FunctionDef) -> Tuple[RetType, ...]:
        returns = self._build(node.returns, RetType)

        if returns is not None and not isinstance(returns, tuple):
            returns = returns,

        return returns

    def _build(self, node: Optional[ast.expr], builder = lambda x: x):
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

        if isinstance(node, (ast.List, ast.Tuple)):
            return functools.reduce(
                lambda acc, item: (*acc, self._build(item, builder)),
                node.elts,
                (),
                )

        raise TypeError(ast.dump(node))
