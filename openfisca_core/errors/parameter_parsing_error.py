import os


class ParameterParsingError(Exception):
    """
    Exception raised when a parameter cannot be parsed.
    """

    def __init__(self, message, file=None, traceback=None):
        """
        :param message: Error message
        :param file: Parameter file which caused the error (optional)
        :param traceback: Traceback (optional)
        """
        if file is not None:
            message = os.linesep.join(
                ["Error parsing parameter file '{}':".format(file), message]
            )
        if traceback is not None:
            message = os.linesep.join([traceback, message])
        super(ParameterParsingError, self).__init__(message)
