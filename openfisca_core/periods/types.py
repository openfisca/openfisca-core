# TODO(<Mauko Quiroga-Alvarado>): Properly resolve metaclass types.
# https://github.com/python/mypy/issues/14033

from collections.abc import Sequence

from openfisca_core.types import DateUnit, Instant, Period

import re

#: Matches "2015", "2015-01", "2015-01-01" but not "2015-13", "2015-12-32".
iso_format = re.compile(r"^\d{4}(-(?:0[1-9]|1[0-2])(-(?:0[1-9]|[12]\d|3[01]))?)?$")

#: Matches "2015", "2015-W01", "2015-W53-1" but not "2015-W54", "2015-W10-8".
iso_calendar = re.compile(r"^\d{4}(-W(0[1-9]|[1-4][0-9]|5[0-3]))?(-[1-7])?$")


class _SeqIntMeta(type):
    def __instancecheck__(self, arg: object) -> bool:
        return (
            bool(arg)
            and isinstance(arg, Sequence)
            and all(isinstance(item, int) for item in arg)
        )


class SeqInt(list[int], metaclass=_SeqIntMeta):  # type: ignore[misc]
    """A sequence of integers.

    Examples:
        >>> isinstance([1, 2, 3], SeqInt)
        True

        >>> isinstance((1, 2, 3), SeqInt)
        True

        >>> isinstance({1, 2, 3}, SeqInt)
        False

        >>> isinstance([1, 2, "3"], SeqInt)
        False

        >>> isinstance(1, SeqInt)
        False

        >>> isinstance([], SeqInt)
        False

    """


class _InstantStrMeta(type):
    def __instancecheck__(self, arg: object) -> bool:
        return isinstance(arg, (ISOFormatStr, ISOCalendarStr))


class InstantStr(str, metaclass=_InstantStrMeta):  # type: ignore[misc]
    """A string representing an instant in string format.

    Examples:
        >>> isinstance("2015", InstantStr)
        True

        >>> isinstance("2015-01", InstantStr)
        True

        >>> isinstance("2015-W01", InstantStr)
        True

        >>> isinstance("2015-W01-12", InstantStr)
        False

        >>> isinstance("week:2015-W01:3", InstantStr)
        False

    """

    __slots__ = ()


class _ISOFormatStrMeta(type):
    def __instancecheck__(self, arg: object) -> bool:
        return isinstance(arg, str) and bool(iso_format.match(arg))


class ISOFormatStr(str, metaclass=_ISOFormatStrMeta):  # type: ignore[misc]
    """A string representing an instant in ISO format.

    Examples:
        >>> isinstance("2015", ISOFormatStr)
        True

        >>> isinstance("2015-01", ISOFormatStr)
        True

        >>> isinstance("2015-01-01", ISOFormatStr)
        True

        >>> isinstance("2015-13", ISOFormatStr)
        False

        >>> isinstance("2015-W01", ISOFormatStr)
        False

    """

    __slots__ = ()


class _ISOCalendarStrMeta(type):
    def __instancecheck__(self, arg: object) -> bool:
        return isinstance(arg, str) and bool(iso_calendar.match(arg))


class ISOCalendarStr(str, metaclass=_ISOCalendarStrMeta):  # type: ignore[misc]
    """A string representing an instant in ISO calendar.

    Examples:
        >>> isinstance("2015", ISOCalendarStr)
        True

        >>> isinstance("2015-W01", ISOCalendarStr)
        True

        >>> isinstance("2015-W11-7", ISOCalendarStr)
        True

        >>> isinstance("2015-W010", ISOCalendarStr)
        False

        >>> isinstance("2015-01", ISOCalendarStr)
        False

    """

    __slots__ = ()


class _PeriodStrMeta(type):
    def __instancecheck__(self, arg: object) -> bool:
        return (
            isinstance(arg, str)
            and ":" in arg
            and isinstance(arg.split(":")[1], InstantStr)
        )


class PeriodStr(str, metaclass=_PeriodStrMeta):  # type: ignore[misc]
    """A string representing a period.

    Examples:
        >>> isinstance("year", PeriodStr)
        False

        >>> isinstance("2015", PeriodStr)
        False

        >>> isinstance("year:2015", PeriodStr)
        True

        >>> isinstance("month:2015-01", PeriodStr)
        True

        >>> isinstance("weekday:2015-W01-1:365", PeriodStr)
        True

        >>> isinstance("2015-W01:1", PeriodStr)
        False

    """

    __slots__ = ()


__all__ = [
    "DateUnit",
    "ISOCalendarStr",
    "ISOFormatStr",
    "Instant",
    "InstantStr",
    "Period",
    "PeriodStr",
    "SeqInt",
]
