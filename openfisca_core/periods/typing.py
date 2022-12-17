# pylint: disable=missing-class-docstring,missing-function-docstring

from __future__ import annotations

from typing_extensions import Protocol

from pendulum.datetime import Date


class Add(Protocol):
    def __call__(self, years: int, months: int, week: int, days: int) -> Date:
        ...


class Plural(Protocol):
    def __call__(self, text: str, count: str | int | None = None) -> str:
        ...
