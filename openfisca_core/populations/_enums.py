from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple

import enum

import strenum

from openfisca_core import types as t


class Option(strenum.StrEnum):
    ADD = enum.auto()
    DIVIDE = enum.auto()

    def __contains__(self, option: str) -> bool:
        return option.upper() is self


class Calculate(NamedTuple):
    variable: t.VariableName
    period: t.Period
    option: None | Sequence[Option]


__all__ = ["Calculate", "Option"]
