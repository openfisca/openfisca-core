from __future__ import annotations

import textwrap
from typing import Any, Generator, Sequence, Set, Tuple, Type, TypeVar

from ._builder import Contract, ContractBuilder
from ._protocols import SupportsParsing
from ._repo import Repo

A = TypeVar("A", bound = "SupportsParsing")
B = TypeVar("B", bound = "SupportsParsing")
P = TypeVar("P", bound = "Parser")


class ActualParser:
    """Parses actual files.

    Attributes:
        contracts: The list of built contracts.
        to_parse: The list of files to parse.
        builder: A :class:`.ContractBuilder` instance.
        repo: A :class:`.Repo` instance.

    Examples:
        >>> import os

        >>> this = os.path.relpath(__file__)
        >>> this
        'openfisca_tasks/_parser.py'

        >>> parser = Parser().actual
        >>> parser.to_parse = {this}
        >>> parser.builder = ContractBuilder((this,))

        >>> with parser as parsing:
        ...     count, total = next(parsing)

        >>> count
        1

        >>> total
        1

        >>> next(iter(parser.contracts)).file
        'openfisca_tasks/_parser.py'

    .. versionadded:: 36.1.0

    """

    contracts: Sequence[Contract]
    to_parse: Set[str]
    builder: ContractBuilder
    repo: Repo

    def __get__(self: A, parser: P, __type: Type[P]) -> A:
        self.to_parse = set(parser.actual_files) & set(parser.changed_files)
        self.builder = ContractBuilder(tuple(self.to_parse))
        return self

    def __enter__(self) -> Generator[Tuple[int, ...], None, None]:
        for file in self.builder.files:
            self(file)
            yield self.builder.count, self.builder.total

    def __exit__(self, *__: Any) -> None:
        self.contracts = self.builder.contracts

    def __call__(self, file: str) -> None:
        with open(file, "r") as f:
            source: str = textwrap.dedent(f.read())
            self.builder(source)


class BeforeParser:
    """Parses files from the last tagged commit.

    Attributes:
        contracts: The list of built contracts.
        to_parse: The list of files to parse.
        builder: A :class:`.ContractBuilder` instance.
        repo: A :class:`.Repo` instance.

    Examples:
        >>> that = "openfisca_core/__init__.py"
        >>> parser = Parser().before
        >>> parser.to_parse = {that}
        >>> parser.builder = ContractBuilder((that,))

        >>> with parser as parsing:
        ...     count, total = next(parsing)

        >>> count
        1

        >>> total
        1

        >>> parser.contracts
        ()

    .. versionadded:: 36.1.0

    """

    contracts: Sequence[Contract]
    to_parse: Set[str]
    builder: ContractBuilder
    repo: Repo

    def __get__(self: B, parser: P, __type: Type[P]) -> B:
        self.to_parse = set(parser.before_files) & set(parser.changed_files)
        self.builder = ContractBuilder(tuple(self.to_parse))
        self.repo = parser.repo
        return self

    def __enter__(self) -> Generator[Tuple[int, ...], None, None]:
        for file in self.builder.files:
            self(file)
            yield self.builder.count, self.builder.total

    def __exit__(self, *__: Any) -> None:
        self.contracts = self.builder.contracts

    def __call__(self, file: str) -> None:
        content: str = self.repo.files.show(file)
        source: str = textwrap.dedent(content)
        self.builder(source)


class Parser:
    """Wrapper around the repo and the contract builder.

    Attributes:
        actual_files: The current list of tracked files.
        before_files: The list of tracked files since the last tagged version.
        changed_files: The list of files changed since the last tagged version.
        repo: A :class:`.Repo` instance.
        actual: An :class:`.ActualParser` instance.
        before: An :class:`.BeforeParser` instance.

    Examples:
        >>> import os

        >>> this = os.path.relpath(__file__)
        >>> this
        'openfisca_tasks/_parser.py'

        >>> parser = Parser()

        >>> this in parser.actual_files
        True

        >>> "openfisca_core/__init__.py" in parser.before_files
        True

    .. versionadded:: 36.1.0

    """

    actual_files: Sequence[str]
    before_files: Sequence[str]
    changed_files: Sequence[str]

    repo = Repo()
    actual: SupportsParsing = ActualParser()
    before: SupportsParsing = BeforeParser()

    def __init__(self) -> None:
        self.actual_files = self.repo.files.actual()
        self.before_files = self.repo.files.before()
        self.changed_files = self.repo.files.changed()
