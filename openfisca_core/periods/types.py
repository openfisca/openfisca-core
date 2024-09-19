from __future__ import annotations

from typing import NewType, Protocol

from pendulum.datetime import Date

from openfisca_core import types as t

# New types.

#: For example "2000-01".
InstantStr = NewType("InstantStr", str)

#: For example "1:2000-01-01:day".
PeriodStr = NewType("PeriodStr", str)


# Periods


class DateUnit(t.DateUnit, Protocol):
    ...


class Instant(t.Instant, Protocol):
    @property
    def year(self) -> int:
        ...

    @property
    def month(self) -> int:
        ...

    @property
    def day(self) -> int:
        ...

    @property
    def date(self) -> Date:
        ...

    def __lt__(self, other: object, /) -> bool:
        ...

    def __le__(self, other: object, /) -> bool:
        ...

    def offset(self, offset: str | int, unit: DateUnit) -> Instant | None:
        ...


class Period(t.Period, Protocol):
    @property
    def size(self) -> int:
        ...

    @property
    def start(self) -> Instant:
        ...

    @property
    def stop(self) -> Instant:
        ...

    def offset(self, offset: str | int, unit: DateUnit | None = None) -> Period:
        ...
