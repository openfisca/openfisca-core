from __future__ import annotations

import os
from collections.abc import Iterable


class SituationParsingError(Exception):
    """Exception raised when the situation provided as an input for a simulation cannot be parsed."""

    def __init__(
        self,
        path: Iterable[str | int],
        message: str,
        code: int | None = None,
    ) -> None:
        message = str(message).strip(os.linesep).replace(os.linesep, " ")
        # Built by hand because dpath.new turns numeric keys such as "2017" into
        # list indexes. Ints are array positions, anything else is a key.
        # See https://github.com/dpath-maintainers/dpath-python/issues/160
        error: dict | list | str = message
        for key in reversed(list(path)):
            if isinstance(key, int):
                error = [None] * key + [error]
            else:
                error = {str(key): error}
        self.error = error
        self.code = code
        Exception.__init__(self, str(self.error))

    def __str__(self) -> str:
        return str(self.error)
