from __future__ import annotations

from enum import EnumMeta

from strenum import StrEnum


class DateUnitMeta(EnumMeta):
    @property
    def isoformat(self) -> tuple[DateUnit, ...]:
        """Creates a :obj:`tuple` of ``key`` with isoformat items.

        Returns:
            tuple(str): A :obj:`tuple` containing the ``keys``.

        Examples:
            >>> DateUnit.isoformat
            (<DateUnit.DAY: 'day'>, <DateUnit.MONTH: 'month'>, <DateUnit.YE...)

            >>> DateUnit.DAY in DateUnit.isoformat
            True

            >>> DateUnit.WEEK in DateUnit.isoformat
            False

        """

        return DateUnit.DAY, DateUnit.MONTH, DateUnit.YEAR

    @property
    def isocalendar(self) -> tuple[DateUnit, ...]:
        """Creates a :obj:`tuple` of ``key`` with isocalendar items.

        Returns:
            tuple(str): A :obj:`tuple` containing the ``keys``.

        Examples:
            >>> DateUnit.isocalendar
            (<DateUnit.WEEKDAY: 'weekday'>, <DateUnit.WEEK: 'week'>, <DateU...)

            >>> DateUnit.WEEK in DateUnit.isocalendar
            True

            >>> "day" in DateUnit.isocalendar
            False

        """

        return DateUnit.WEEKDAY, DateUnit.WEEK, DateUnit.YEAR


class DateUnit(StrEnum, metaclass=DateUnitMeta):
    """The date units of a rule system.

    Examples:
        >>> repr(DateUnit)
        "<enum 'DateUnit'>"

        >>> repr(DateUnit.DAY)
        "<DateUnit.DAY: 'day'>"

        >>> str(DateUnit.DAY)
        'day'

        >>> dict([(DateUnit.DAY, DateUnit.DAY.value)])
        {<DateUnit.DAY: 'day'>: 'day'}

        >>> list(DateUnit)
        [<DateUnit.WEEKDAY: 'weekday'>, <DateUnit.WEEK: 'week'>, <DateUnit.DAY: 'day'>, ...]

        >>> len(DateUnit)
        6

        >>> DateUnit["DAY"]
        <DateUnit.DAY: 'day'>

        >>> DateUnit(DateUnit.DAY)
        <DateUnit.DAY: 'day'>

        >>> DateUnit.DAY in DateUnit
        True

        >>> "day" in list(DateUnit)
        True

        >>> DateUnit.DAY == "day"
        True

        >>> DateUnit.DAY.name
        'DAY'

        >>> DateUnit.DAY.value
        'day'

    .. versionadded:: 35.9.0

    """

    WEEKDAY = "weekday"
    WEEK = "week"
    DAY = "day"
    MONTH = "month"
    YEAR = "year"
    ETERNITY = "eternity"
