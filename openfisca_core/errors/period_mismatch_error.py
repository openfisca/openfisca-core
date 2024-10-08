class PeriodMismatchError(ValueError):
    """Exception raised when one tries to set a variable value for a period that doesn't match its definition period."""

    def __init__(self, variable_name: str, period, definition_period, message) -> None:
        self.variable_name = variable_name
        self.period = period
        self.definition_period = definition_period
        self.message = message
        ValueError.__init__(self, self.message)
