from __future__ import annotations

from typing import Any

from ._units import DAY, MONTH, YEAR
from .typing import Instant

LEARN_MORE = (
    "Learn more about legal period formats in OpenFisca: "
    "<https://openfisca.org/doc/coding-the-legislation/35_html#periods-in-simulations>."
    )


class DateUnitValueError(ValueError):
    """Raised when a date unit's value is not valid."""

    def __init__(self, value: Any) -> None:
        super().__init__(
            f"'{value}' is not a valid ISO format date unit. ISO format date "
            f"units are any of: '{DAY}', '{MONTH}', or '{YEAR}'. {LEARN_MORE}"
            )


class InstantFormatError(ValueError):
    """Raised when an instant's format is not valid (ISO format)."""

    def __init__(self, value: Any) -> None:
        super().__init__(
            f"'{value}' is not a valid instant. Instants are described using "
            "the 'YYYY-MM-DD' format, for instance '2015-06-15'. {LEARN_MORE}"
            )


class InstantValueError(ValueError):
    """Raised when an instant's values are not valid."""

    def __init__(self, value: Any) -> None:
        super().__init__(
            f"Invalid instant: '{value}' has a length of {len(value)}. "
            "Instants are described using the 'YYYY-MM-DD' format, for "
            "instance '2015-06-15', therefore their length has to be within "
            f" the following range: 1 <= length <= 3. {LEARN_MORE}"
            )


class InstantTypeError(TypeError):
    """Raised when an instant's type is not valid."""

    def __init__(self, value: Any) -> None:
        super().__init__(
            f"Invalid instant: {value} of type {type(value)}, expecting an "
            f"{type(Instant)}, {type(tuple)}, or {type(list)}. {LEARN_MORE}"
            )


class PeriodFormatError(ValueError):
    """Raised when a period's format is not valid ."""

    def __init__(self, value: Any) -> None:
        super().__init__(
            f"'{value}' is not a valid period. Periods are described using "
            "the 'unit:YYYY-MM-DD:size' format, for instance "
            f"'day:2023-01-15:3'. {LEARN_MORE}"
            )


class OffsetTypeError(TypeError):
    """Raised when an offset's type is not valid."""

    def __init__(self, value: Any) -> None:
        super().__init__(
            f"Invalid offset: {value} of type {type(value)}, expecting an "
            f"{type(int)}. {LEARN_MORE}"
            )
