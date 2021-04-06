class ParameterNotFoundError(AttributeError):
    """
    Exception raised when a parameter is not found in the parameters.
    """

    def __init__(self, name, instant_str, variable_name = None):
        """
        :param name: Name of the parameter
        :param instant_str: Instant where the parameter does not exist, in the format `YYYY-MM-DD`.
        :param variable_name: If the parameter was queried during the computation of a variable, name of that variable.
        """
        self.name = name
        self.instant_str = instant_str
        self.variable_name = variable_name
        message = "The parameter '{}'".format(name)
        if variable_name is not None:
            message += " requested by variable '{}'".format(variable_name)
        message += (
            " was not found in the {} tax and benefit system."
            ).format(instant_str)
        super(ParameterNotFoundError, self).__init__(message)
