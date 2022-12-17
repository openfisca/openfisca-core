# pylint: disable=missing-class-docstring,missing-function-docstring

from __future__ import annotations

from typing import TypeVar
from typing_extensions import Protocol

T = TypeVar("T", covariant = True)
U = TypeVar("U")


class Add(Protocol[T]):
    def __call__(self, years: int, months: int, week: int, days: int) -> T: ...


class Plural(Protocol[U]):
    def __call__(self, text: U, count: str | int | None = None) -> U: ...
