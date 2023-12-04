from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class _Axis:
    """Base data class for axes (no domain logic).

    Examples:
       >>> axis = _Axis(name = "salary", count = 3, min = 0, max = 3000)

       >>> axis
       _Axis(name='salary', count=3, min=0, max=3000, period=None, index=0)

       >>> axis.name
       'salary'

    """

    #: The name of the Variable whose values are to be expanded.
    name: str

    #: The Number of "steps" to take when expanding Variable (between `min` and
    # `max`, we create a line and split it in `count` number of parts).
    count: int

    #: The starting numerical value for the Axis expansion.
    min: float

    #: The up-to numerical value for the Axis expansion.
    max: float

    #: The period at which the expansion will take place over.
    period: str | int | None = None

    #: Axis position relative to other equidistant axes.
    index: int = 0
