class PeriodMismatchError(ValueError):
    """
    Exception raised when one tries to set a variable value for a period that doesn't match its definition period
    """

    def __init__(self, variable_name, period, definition_period, message):
        self.variable_name = variable_name
        self.period = period
        self.definition_period = definition_period
        self.message = message
        ValueError.__init__(self, self.message)
