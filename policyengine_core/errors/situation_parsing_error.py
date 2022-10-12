import os

import dpath.util


class SituationParsingError(Exception):
    """
    Exception raised when the situation provided as an input for a simulation cannot be parsed
    """

    def __init__(self, path, message, code = None):
        self.error = {}
        dpath_path = '/'.join([str(item) for item in path])
        message = str(message).strip(os.linesep).replace(os.linesep, ' ')
        dpath.util.new(self.error, dpath_path, message)
        self.code = code
        Exception.__init__(self, str(self.error))

    def __str__(self):
        return str(self.error)
