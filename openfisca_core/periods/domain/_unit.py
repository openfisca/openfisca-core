import enum


class DateUnit(str, enum.Enum):
    """The date units of a rule system.

    Examples:
        >>> repr(DateUnit)
        "<enum 'DateUnit'>"

        >>> repr(DateUnit.DAY)
        "'day'"

        >>> str(DateUnit.DAY)
        'day'

        >>> dict([(DateUnit.DAY, DateUnit.DAY.value)])
        {'day': 'day'}

        >>> list(DateUnit)
        ['day', 'month', 'year', 'eternity']

        >>> len(DateUnit)
        4

        >>> DateUnit["DAY"]
        'day'

        >>> DateUnit(DateUnit.DAY)
        'day'

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

    .. versionadded:: 39.1.0

    """

    DAY = "day"
    MONTH = "month"
    YEAR = "year"
    ETERNITY = "eternity"

    def __repr__(self) -> str:
        return self.value.__repr__()

    def __str__(self) -> str:
        return self.value.__str__()
