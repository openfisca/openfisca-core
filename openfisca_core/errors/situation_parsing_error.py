from __future__ import annotations

from collections.abc import Iterable

import os

import dpath.util


class SituationParsingError(Exception):
    """Exception raised when the situation provided as an input for a simulation cannot be parsed."""

    def __init__(
        self,
        path: Iterable[str],
        message: str,
        code: int | None = None,
    ) -> None:
        self.error = {}
        dpath_path = "/".join([str(item) for item in path])
        message = str(message).strip(os.linesep).replace(os.linesep, " ")
        dpath.util.new(self.error, dpath_path, message)
        self.code = code
        Exception.__init__(self, str(self.error))

    def __str__(self) -> str:
        return str(self.error)
