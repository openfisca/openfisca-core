#! /usr/bin/env python

from __future__ import annotations

import os
import sys
import typing
from packaging import version
from typing import NoReturn, Union

import numpy

if typing.TYPE_CHECKING:
    from packaging.version import LegacyVersion, Version


def prev() -> NoReturn:
    release = _installed().release

    if release is None:
        sys.exit(os.EX_DATAERR)

    major, minor, _ = release

    if minor == 0:
        sys.exit(os.EX_DATAERR)

    minor -= 1
    print(f"{major}.{minor}.0")  # noqa: T201
    sys.exit(os.EX_OK)


def _installed() -> Union[LegacyVersion, Version]:
    return version.parse(numpy.__version__)


if __name__ == "__main__":
    globals()[sys.argv[1]]()
