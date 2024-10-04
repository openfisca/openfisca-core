import os


class ParameterParsingError(Exception):
    """Exception raised when a parameter cannot be parsed."""

    def __init__(self, message, file=None, traceback=None) -> None:
        """:param message: Error message
        :param file: Parameter file which caused the error (optional)
        :param traceback: Traceback (optional)
        """
        if file is not None:
            message = os.linesep.join(
                [f"Error parsing parameter file '{file}':", message],
            )
        if traceback is not None:
            message = os.linesep.join([traceback, message])
        super().__init__(message)
