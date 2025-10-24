from pendulum.parsing.exceptions import ParserError


class InstantError(ValueError):
    """Raised when an invalid instant-like is provided."""

    def __init__(self, value: str) -> None:
        msg = (
            f"'{value}' is not a valid instant string. Instants are described "
            "using either the 'YYYY-MM-DD' format, for instance '2015-06-15', "
            "or the 'YYYY-Www-D' format, for instance '2015-W24-1'."
        )
        super().__init__(msg)


class PeriodError(ValueError):
    """Raised when an invalid period-like is provided."""

    def __init__(self, value: str) -> None:
        msg = (
            "Expected a period (eg. '2017', 'month:2017-01', 'week:2017-W01-1:3', "
            f"...); got: '{value}'. Learn more about legal period formats in "
            "OpenFisca: <https://openfisca.org/doc/coding-the-legislation/35_periods.html#periods-in-simulations>."
        )
        super().__init__(msg)


__all__ = ["InstantError", "ParserError", "PeriodError"]
