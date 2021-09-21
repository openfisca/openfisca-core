from __future__ import annotations

import enum
from typing import Any, Tuple, TypeVar

from openfisca_core.indexed_enums import Enum

T = TypeVar("T", bound = "DateUnit")


class DateUnitMeta(enum.EnumMeta):

    def __contains__(self, item: Any) -> bool:
        if isinstance(item, str):
            return super().__contains__(self[item.upper()])

        return super().__contains__(item)

    def __getitem__(self, key: object) -> T:
        if not isinstance(key, (int, slice, str, DateUnit)):
            return NotImplemented

        if isinstance(key, (int, slice)):
            return self[self.__dict__["_member_names_"][key]]

        if isinstance(key, str):
            return super().__getitem__(key.upper())

        return super().__getitem__(key.value.upper())

    @property
    def isoformat(self) -> Tuple[DateUnit, ...]:
        """Creates a :obj:`tuple` of ``key`` with isoformat items.

        Returns:
            tuple(str): A :obj:`tuple` containing the ``keys``.

        Examples:
            >>> DateUnit.isoformat
            (<DateUnit.DAY(day)>, <DateUnit.MONTH(month)>, <DateUnit.YEAR(y...)

            >>> DateUnit.DAY in DateUnit.isoformat
            True

            >>> "DAY" in DateUnit.isoformat
            True

            >>> "day" in DateUnit.isoformat
            True

            >>> DateUnit.WEEK in DateUnit.isoformat
            False

        """

        return DateUnit.DAY, DateUnit.MONTH, DateUnit.YEAR

    @property
    def isocalendar(self) -> Tuple[DateUnit, ...]:
        """Creates a :obj:`tuple` of ``key`` with isocalendar items.

        Returns:
            tuple(str): A :obj:`tuple` containing the ``keys``.

        Examples:
            >>> DateUnit.isocalendar
            (<DateUnit.WEEK_DAY(week_day)>, <DateUnit.WEEK(week)>, <DateUni...)

            >>> DateUnit.WEEK in DateUnit.isocalendar
            True

            >>> "WEEK" in DateUnit.isocalendar
            True

            >>> "week" in DateUnit.isocalendar
            True

            >>> "day" in DateUnit.isocalendar
            False

        """

        return DateUnit.WEEK_DAY, DateUnit.WEEK, DateUnit.YEAR


class DateUnit(Enum, metaclass = DateUnitMeta):
    """The date units of a rule system.

    Attributes:
        index (:obj:`int`): The ``index`` of each item.
        name (:obj:`str`): The ``name`` of each item.
        value (tuple(str, int)): The ``value`` of each item.

    Examples:
        >>> repr(DateUnit)
        "<enum 'DateUnit'>"

        >>> repr(DateUnit.DAY)
        '<DateUnit.DAY(day)>'

        >>> str(DateUnit.DAY)
        'day'

        >>> dict([(DateUnit.DAY, DateUnit.DAY.value)])
        {<DateUnit.DAY(day)>: 'day'}

        >>> list(DateUnit)
        [<DateUnit.WEEK_DAY(week_day)>, <DateUnit.WEEK(week)>, <DateUnit.DA...]

        >>> len(DateUnit)
        6

        >>> DateUnit["DAY"]
        <DateUnit.DAY(day)>

        >>> DateUnit["day"]
        <DateUnit.DAY(day)>

        >>> DateUnit[2]
        <DateUnit.DAY(day)>

        >>> DateUnit[-4]
        <DateUnit.DAY(day)>

        >>> DateUnit[DateUnit.DAY]
        <DateUnit.DAY(day)>

        >>> DateUnit("day")
        <DateUnit.DAY(day)>

        >>> DateUnit.DAY in DateUnit
        True

        >>> "DAY" in DateUnit
        True

        >>> "day" in DateUnit
        True

        >>> DateUnit.DAY == DateUnit.DAY
        True

        >>> "DAY" == DateUnit.DAY
        True

        >>> "day" == DateUnit.DAY
        True

        >>> DateUnit.DAY < DateUnit.DAY
        False

        >>> DateUnit.DAY > DateUnit.DAY
        False

        >>> DateUnit.DAY <= DateUnit.DAY
        True

        >>> DateUnit.DAY >= DateUnit.DAY
        True

        >>> "DAY" < DateUnit.DAY
        False

        >>> "DAY" > DateUnit.DAY
        False

        >>> "DAY" <= DateUnit.DAY
        True

        >>> "DAY" >= DateUnit.DAY
        True

        >>> "day" < DateUnit.DAY
        False

        >>> "day" > DateUnit.DAY
        False

        >>> "day" <= DateUnit.DAY
        True

        >>> "day" >= DateUnit.DAY
        True

        >>> DateUnit.DAY.index
        2

        >>> DateUnit.DAY.name
        'DAY'

        >>> DateUnit.DAY.value
        'day'

    .. versionadded:: 35.9.0

    """

    # Attributes

    index: int
    name: str
    value: str

    # Members

    WEEK_DAY = "week_day"
    WEEK = "week"
    DAY = "day"
    MONTH = "month"
    YEAR = "year"
    ETERNITY = "eternity"

    __hash__ = Enum.__hash__

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, str):
            return super().__eq__(other)

        return self.value == other.lower()

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, str):
            return super().__ne__(other)

        return self.value != other.lower()

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, str):
            return super().__lt__(other)

        return self.index < DateUnit[other].index

    def __le__(self, other: object) -> bool:
        if not isinstance(other, str):
            return super().__le__(other)

        return self.index <= DateUnit[other].index

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, str):
            return super().__gt__(other)

        return self.index > DateUnit[other].index

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, str):
            return super().__ge__(other)

        return self.index >= DateUnit[other].index

    def upper(self) -> str:
        """Uppercases the :class:`.DateUnit`.

        Returns:
            :obj:`str`: The uppercased :class:`.Unit`.

        Examples:
            >>> DateUnit.DAY.upper()
            'DAY'

        """

        return self.value.upper()

    def lower(self) -> str:
        """Lowecases the :class:`.DateUnit`.

        Returns:
            :obj:`str`: The lowercased :class:`.Unit`.

        Examples:
            >>> DateUnit.DAY.lower()
            'day'

        """

        return self.value.lower()
