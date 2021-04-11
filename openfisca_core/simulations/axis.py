from __future__ import annotations

import dataclasses
from typing import Optional, Union


@dataclasses.dataclass(frozen = True)
class Axis:
    """
    Base data class for axes (no domain logic).

    Attributes:

        name:   The name of the :class:`openfisca_core.variables.Variable`
                whose values are to be expanded.
        count:  The Number of "steps" to take when expanding a
                :class:`openfisca_core.variables.Variable` (between
                :attr:`min_` and :attr:`max_`, we create a line and split it in
                :attr:`count` number of parts).
        min:    The starting numerical value for the :class:`Axis` expansion.
        max:    The up-to numerical value for the :class:`Axis` expansion.
        period: The period at which the expansion will take place over.
        index:  The :class:`Axis` position relative to other equidistant axes.

    Usage:

       >>> axis = Axis(name = "salary", count = 3, min = 0, max = 3000)
       >>> axis
       Axis(name='salary', count=3, min=0, max=3000, period=None, index=0)

       >>> axis.name
       'salary'

    Testing:

        pytest tests/core/test_axes.py openfisca_core/simulations/axis.py

    .. versionadded:: 35.4.0
    """

    name: str
    count: int
    min: Union[int, float]
    max: Union[int, float]
    period: Optional[Union[int, str]] = dataclasses.field(default = None)
    index: int = dataclasses.field(default = 0)
