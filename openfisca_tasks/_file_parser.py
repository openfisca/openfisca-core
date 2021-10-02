from __future__ import annotations

import textwrap
from typing import Any, Generator, Sequence, Set, Type

from ._contract_builder import Contract, ContractBuilder
from ._repo import Repo


class ActualParser:
    contracts: Sequence[Contract]
    to_parse: Set[str]
    builder: ContractBuilder

    def __get__(
            self,
            parser: FileParser,
            __type: Type[FileParser],
            ) -> ActualParser:
        self.to_parse = set(parser.actual_files) & set(parser.changed_files)
        self.builder = ContractBuilder(tuple(self.to_parse))
        return self

    def __enter__(self) -> Generator:
        for file in self.builder.files:
            self.parse(file)
            yield self.builder.count, self.builder.total

    def __exit__(self, *__: Any) -> None:
        self.contracts = self.builder.contracts

    def parse(self, file: str) -> None:
        with open(file, "r") as f:
            source: str = textwrap.dedent(f.read())
            self.builder(source)


class BeforeParser:
    contracts: Sequence[Contract]
    to_parse: Set[str]
    builder: ContractBuilder
    repo: Repo

    def __get__(
            self,
            parser: FileParser,
            __type: Type[FileParser],
            ) -> BeforeParser:
        self.to_parse = set(parser.before_files) & set(parser.changed_files)
        self.builder = ContractBuilder(tuple(self.to_parse))
        self.repo = parser.repo
        return self

    def __enter__(self) -> Generator:
        for file in self.builder.files:
            self.parse(file)
            yield self.builder.count, self.builder.total

    def __exit__(self, *__: Any) -> None:
        self.contracts = self.builder.contracts

    def parse(self, file: str) -> None:
        content: str = self.repo.files.show(file)
        source: str = textwrap.dedent(content)
        self.builder(source)


class FileParser:

    actual_files: Sequence[str]
    before_files: Sequence[str]
    changed_files: Sequence[str]

    repo: Repo = Repo()
    actual: ActualParser = ActualParser()
    before: BeforeParser = BeforeParser()

    def __init__(self) -> None:
        self.actual_files = self.repo.files.actual()
        self.before_files = self.repo.files.before()
        self.changed_files = self.repo.files.changed()
