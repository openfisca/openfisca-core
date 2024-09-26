from pendulum.parsing.exceptions import ParserError


class InstantError(ValueError):
    """Raised when an invalid instant-like is provided."""

    def __init__(self, value: str) -> None:
        msg = (
            f"'{value}' is not a valid instant. Instants are described "
            "using the 'YYYY-MM-DD' format, for instance '2015-06-15'."
        )
        super().__init__(msg)


__all__ = ["InstantError", "ParserError"]
