from __future__ import annotations

import datetime
import typing
from typing import Dict, List, Optional, Sequence, Union

from typing_extensions import Literal

from openfisca_core import commons, periods
from openfisca_core.periods import Instant, Period

from .date_unit import DateUnit

DOC_URL = "https://openfisca.org/doc/coding-the-legislation"

InstantLike = Union[
    Sequence[Union[int, str]],
    datetime.date,
    Instant,
    Period,
    int,
    str,
]

PeriodLike = Union[
    Literal["ETERNITY", "eternity"],
    datetime.date,
    Instant,
    Period,
    int,
    str,
]


@typing.overload
def instant(instant: None) -> None:
    ...


@typing.overload
def instant(instant: InstantLike) -> Instant:
    ...


def instant(instant: Optional[InstantLike] = None) -> Optional[Instant]:
    """Return a new instant, aka a triple of integers (year, month, day).

    Args:
        instant: An ``instant-like`` object.

    Returns:
        None: When ``instant`` is None.
        :obj:`.Instant`: Otherwise.

    Raises:
        :exc:`ValueError`: When the arguments were invalid, like "2021-32-13".

    Examples:

    >>> instant()

    >>> instant((2021,))
    <Instant(2021, 1, 1)>

    >>> instant((2021, 9))
    <Instant(2021, 9, 1)>

    >>> instant(datetime.date(2021, 9, 16))
    <Instant(2021, 9, 16)>

    >>> instant(Instant((2021, 9, 16)))
    <Instant(2021, 9, 16)>

    >>> instant(Period((DateUnit.YEAR.value, Instant((2021, 9, 16)), 1)))
    <Instant(2021, 9, 16)>

    >>> instant(2021)
    <Instant(2021, 1, 1)>

    >>> instant("2021")
    <Instant(2021, 1, 1)>

    >>> instant("day:2021-9-16:3")
    <Instant(2021, 9, 16)>


    """

    if instant is None:
        return None

    if isinstance(instant, Instant):
        return instant

    #: See: :attr`.Period.start`.
    if isinstance(instant, Period):
        return instant.start

    #: For example ``2021`` gives ``<Instant(2021, 1, 1)>``.
    if isinstance(instant, int):
        return Instant((instant, 1, 1))

    #: For example ``datetime.date(2021, 9, 16)``.
    if isinstance(instant, datetime.date):
        return Instant((instant.year, instant.month, instant.day))

    try:
        #: For example if ``instant`` is ``["2014"]``, we will:
        #:
        #: 1. Try to cast each element to an :obj:`int`.
        #
        #: 2. Add a date unit recursively (``month``, then ``day``).
        #:
        if isinstance(instant, (list, tuple)) and len(instant) < 3:
            return periods.instant([*[int(unit) for unit in instant], 1])

        #: For example if ``instant`` is ``["2014", 9, 12, 32]``, we will:
        #:
        #: 1. Select the first three elements of the collection.
        #
        #: 2. Try to cast those three elements to an :obj:`int`.
        #:
        if isinstance(instant, (list, tuple)):
            return Instant(tuple(int(unit) for unit in instant[0:3]))

        #: Up to this point, if ``instant`` is not a :obj:`str`, we desist.
        if not isinstance(instant, str):
            raise ValueError

        #: We look for ``fragments``, for example ``day:2014:3``:
        #:
        #: - If there are, we split and call :func:`.instant` recursively.
        #:
        #: - If there are not, we continue.
        #:
        #: See :meth:`.Period.get_subperiods` and :attr:`.Period.size`.
        #:
        if instant.find(":") != -1:
            return periods.instant(instant.split(":")[1])

        #: We assume we're dealing with a date in the ISO format, so:
        #:
        #: - If we can't decompose ``instant``, we call :func:`.instant`
        #:   recursively, for example given ``"2014"``` we will call
        #:   ``periods.instant(["2014"])``.
        #:
        #:  - Otherwise, we split ``instant`` and then call :func:`.instant`
        #:   recursively, for example given ``"2014-9"`` we will call
        #:   ``periods.instant(["2014", "9"])``.
        #:
        if instant.find("-") == -1:
            return periods.instant([instant])

        return periods.instant(instant.split("-"))

    except ValueError:
        raise ValueError(
            f"'{instant}' is not a valid instant. Instants are described "
            "using the 'YYYY-MM-DD' format, for example: '2015-06-15'. "
            "Learn more about legal period formats in "
            f"OpenFisca: <{DOC_URL}/35_periods.html#periods-in-simulations>."
            )


@typing.overload
def instant_date(instant: None) -> None:
    ...


@typing.overload
def instant_date(instant: Instant) -> datetime.date:
    ...


@commons.deprecated(since = "35.9.0", expires = "the future")
def instant_date(instant: Optional[Instant] = None) -> Optional[datetime.date]:
    """Returns the date representation of an :class:`.Instant`.

    Args:
        instant (:obj:`.Instant`, optional):

    Returns:
        None: When ``instant`` is None.
        :obj:`datetime.date`: Otherwise.

    Examples:
        >>> instant_date()

        >>> instant_date(Instant((2021, 1, 1)))
        datetime.date(2021, 1, 1)

    .. deprecated:: 35.9.0
        :func:`.instant_date` has been deprecated and will be
        removed in the future. The functionality is now provided by
        :attr:`.Instant.date` (cache included).

    """

    if instant is None:
        return None

    return instant.date


def period(value: PeriodLike) -> Period:
    """Returns a new period, aka a triple (unit, start_instant, size).

    Args:
        value: A ``period-like`` object.

    Returns:
        :obj:`.Period`: A period.

    Raises:
        :exc:`ValueError`: When the arguments were invalid, like "2021-32-13".


    >>> period(Period(("year", Instant((2021, 1, 1)), 1)))
    <Period(('year', <Instant(2021, 1, 1)>, 1))>

    >>> period(Instant((2021, 1, 1)))
    <Period(('day', <Instant(2021, 1, 1)>, 1))>

    >>> period("eternity")
    <Period(('eternity', <Instant(1, 1, 1)>, inf))>

    >>> period(datetime.date(2021, 9, 16))
    <Period(('day', <Instant(2021, 9, 16)>, 1))>

    >>> period(2021)
    <Period(('year', <Instant(2021, 1, 1)>, 1))>

    >>> period("2014")
    <Period(('year', <Instant(2014, 1, 1)>, 1))>

    >>> period("year:2014")
    <Period(('year', <Instant(2014, 1, 1)>, 1))>

    >>> period("month:2014-2")
    <Period(('month', <Instant(2014, 2, 1)>, 1))>

    >>> period("year:2014-2")
    <Period(('year', <Instant(2014, 2, 1)>, 1))>

    >>> period("day:2014-2-2")
    <Period(('day', <Instant(2014, 2, 2)>, 1))>

    >>> period("day:2014-2-2:3")
    <Period(('day', <Instant(2014, 2, 2)>, 3))>

    """

    date: str
    index: int
    input_unit: str
    instant: Instant
    instant_unit: DateUnit
    period_unit: DateUnit
    rest: List[str]
    size: int

    if isinstance(value, Period):
        return value

    #: We return a "day-period", for example
    #: ``<Period(('day', <Instant(2021, 1, 1)>, 1))>``.
    #:
    if isinstance(value, Instant):
        return Period((DateUnit.DAY.value, value, 1))

    #: For example ``datetime.date(2021, 9, 16)``.
    if isinstance(value, datetime.date):
        instant = periods.instant(value)
        return Period((DateUnit.DAY.value, instant, 1))

    #: We return an "eternity-period", for example
    #: ``<Period(('eternity', <Instant(1, 1, 1)>, inf))>``.
    #:
    if value == DateUnit.ETERNITY:
        instant = periods.instant(datetime.date.min)
        return Period((DateUnit.ETERNITY.value, instant, float("inf")))

    #: For example ``2021`` gives
    #: ``<Period(('year', <Instant(2021, 1, 1)>, 1))>``.
    #:
    if isinstance(value, int):
        instant = periods.instant(value)
        return Period((DateUnit.YEAR.value, instant, 1))

    try:
        #: Up to this point, if ``value`` is not a :obj:`str`, we desist.
        if not isinstance(value, str):
            raise ValueError

        #: We calculate the date unit index based on the indexes of
        #: :class:`.DateUnit`.
        #:
        #: So for example if ``value`` is ``"2021-02"``, the result of ``len``
        #: will be ``2``, and we know we're looking to build a month-period.
        #:
        #: ``MONTH`` is the 4th member of :class:`.DateUnit`. Because it is
        #: an :class:`.indexed_enums.Enum`, we know its index is then ``3``.
        #:
        #: Then ``5 - 2`` gives us the index of :obj:`.DateUnit.MONTH`, ``3``.
        #:
        index = DateUnit[-1].index - len(value.split("-"))  # type: ignore
        instant_unit = DateUnit[index]  # type: ignore

        #: We look for ``fragments`` see :func:`.instant`.
        #:
        #: If there are no fragments, we will delegate the next steps to
        #: :func:`.instant`.
        #:
        if value.find(":") == -1:
            instant = periods.instant(value)
            return Period((instant_unit.value, instant, 1))

        #: For example ``month``, ``2014``, and ``1``.
        input_unit, *rest = value.split(":")
        period_unit = DateUnit[input_unit]

        #: Left-most component must be a valid unit: ``day``, ``month``, or
        #: ``year``.
        #:
        if period_unit not in DateUnit.isoformat:
            raise ValueError

        #: Reject ambiguous periods, such as ``month:2014``.
        if instant_unit > period_unit:
            raise ValueError

        #: Now that we have the ``unit``, we will create an ``instant``.
        date, *rest = rest
        instant = periods.instant(value)

        #: Periods like ``year:2015-03`` have, by default, a size of 1.
        if not rest:
            return Period((period_unit.value, instant, 1))

        #: If provided, let's make sure the ``size`` is an integer.
        #: We also ignore any extra element, so for example if the provided
        #: ``value`` is ``"year:2021:3:asdf1234"`` we will ignore ``asdf1234``.
        size = int(rest[0])

        return Period((period_unit.value, instant, size))

    except ValueError:
        raise ValueError(
            "Expected a period (eg. '2017', '2017-01', '2017-01-01', ...); "
            f"got: '{value}'. Learn more about legal period formats in "
            f"OpenFisca: <{DOC_URL}/35_periods.html#periods-in-simulations>."
            )


def key_period_size(period: Period) -> str:
    """Defines a key in order to sort periods by length.

    It uses two aspects: first, ``unit``, then, ``size``.

    Args:
        period: An :mod:`.openfisca_core` :obj:`.Period`.

    Returns:
        :obj:`str`: A string.

    Examples:
        >>> instant = Instant((2021, 9, 14))

        >>> period = Period((DateUnit.DAY, instant, 1))
        >>> key_period_size(period)
        '2_1'

        >>> period = Period(("month", instant, 2))
        >>> key_period_size(period)
        '3_2'

        >>> period = Period(("Year", instant, 3))
        >>> key_period_size(period)
        '4_3'

        >>> period = Period(("ETERNITY", instant, 4))
        >>> key_period_size(period)
        '5_4'

    .. versionchanged:: 35.9.0
        Hereafter uses :attr:`.Unit.weight`.

    """

    unit: Union[DateUnit, str]
    size: int

    unit, _, size = period

    if isinstance(unit, str):
        unit = DateUnit[unit]

    return f"{unit.index}_{size}"


@commons.deprecated(since = "35.9.0", expires = "the future")
def unit_weights() -> Dict[str, int]:
    """Finds the weight of each date unit.

    Returns:
        dict(str, int): A dictionary with the corresponding values.

    Examples:
        >>> unit_weights()
        {'week_day': 0, 'week': 1, 'day': 2, 'month': 3, 'year': 4, 'eterni...}

    .. deprecated:: 35.9.0
        :func:`.unit_weights` has been deprecated and will be
        removed in the future. The functionality is now provided by
        :func:`.Unit.weights`.

    """

    return {enum.value: enum.index for enum in DateUnit}


@commons.deprecated(since = "35.9.0", expires = "the future")
def unit_weight(unit: DateUnit) -> Optional[int]:
    """Finds the weight of a specific date unit.

    Args:
        unit: The unit to find the weight for.

    Returns:
        int: The weight.

    Examples:
        >>> unit_weight(DateUnit.DAY)
        2

        >>> unit_weight('DAY')
        2

        >>> unit_weight('day')
        2

    .. deprecated:: 35.9.0
        :func:`.unit_weight` has been deprecated and will be
        removed in the future. The functionality is now provided by
        :attr:`.Unit.weight`.

    """

    if isinstance(unit, str):
        unit = DateUnit[unit]

    return unit.index


@commons.deprecated(since = "35.9.0", expires = "the future")
def N_(message):
    """???"""

    return message
