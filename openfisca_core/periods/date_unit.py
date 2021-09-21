from __future__ import annotations

import enum
from typing import Tuple, TypeVar

from openfisca_core.indexed_enums import Enum

T = TypeVar("T", bound = "DateUnit")


class DateUnitMeta(enum.EnumMeta):

    def __contains__(self, item: object) -> bool:
        if not isinstance(item, (str, int, DateUnit)):
            return NotImplemented

        if isinstance(item, str):
            return super().__contains__(self[item])

        if isinstance(item, int):
            return super().__contains__(self[item])

        return super().__contains__(item)

    def __getitem__(self, key: object) -> T:
        if not isinstance(key, (str, int, slice, DateUnit)):
            return NotImplemented

        if isinstance(key, str):
            return super().__getitem__(key.upper())

        if isinstance(key, (int, slice)):
            return self[self.__dict__["_member_names_"][key]]

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

        >>> DateUnit.DAY == DateUnit.DAY
        True

        >>> DateUnit.DAY < DateUnit.DAY
        False

        >>> DateUnit.DAY > DateUnit.DAY
        False

        >>> DateUnit.DAY <= DateUnit.DAY
        True

        >>> DateUnit.DAY >= DateUnit.DAY
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
        if not isinstance(other, (str, int, DateUnit)):
            return NotImplemented

        if isinstance(other, str) and other.upper() in self._member_names_:
            return self.index == DateUnit[other].index

        if isinstance(other, int):
            return self.index == other

        return super().__eq__(other)

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, (str, int, DateUnit)):
            return NotImplemented

        if isinstance(other, str) and other.upper() in self._member_names_:
            return self.index != DateUnit[other].index

        if isinstance(other, int):
            return self.index != other

        return super().__ne__(other)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, (str, int, DateUnit)):
            return NotImplemented

        if isinstance(other, str):
            return self.index < DateUnit[other].index

        if isinstance(other, int):
            return self.index < other

        return super().__lt__(other)

    def __le__(self, other: object) -> bool:
        if not isinstance(other, (str, int, DateUnit)):
            return NotImplemented

        if isinstance(other, str):
            return self.index <= DateUnit[other].index

        if isinstance(other, int):
            return self.index <= other

        return super().__le__(other)

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, (str, int, DateUnit)):
            return NotImplemented

        if isinstance(other, str):
            return self.index > DateUnit[other].index

        if isinstance(other, int):
            return self.index > other

        return super().__gt__(other)

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, (str, int, DateUnit)):
            return NotImplemented

        if isinstance(other, str):
            return self.index >= DateUnit[other].index

        if isinstance(other, int):
            return self.index >= other

        return super().__ge__(other)

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
