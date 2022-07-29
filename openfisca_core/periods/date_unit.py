from strenum import StrEnum


class DateUnit(StrEnum):
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
        [<DateUnit.DAY: 'day'>, <DateUnit.MONTH: 'month'>, ...]

        >>> len(DateUnit)
        4

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

    DAY = "day"
    MONTH = "month"
    YEAR = "year"
    ETERNITY = "eternity"
