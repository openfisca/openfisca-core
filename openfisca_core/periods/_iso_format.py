from __future__ import annotations

from typing import NamedTuple


class ISOFormat(NamedTuple):
    """An implementation of the `parse` protocol."""

    #: The year of the parsed period.
    year: int

    #: The month of the parsed period.
    month: int

    #: The month of the parsed period.
    day: int

    #: The unit of the parsed period, in binary.
    unit: int

    #: The number of fragments in the parsed period.
    shape: int
