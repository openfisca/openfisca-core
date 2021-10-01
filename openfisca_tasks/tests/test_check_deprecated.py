import inspect
import os
import sys
import tempfile
from typing import NamedTuple

import pytest

from openfisca_tasks import CheckDeprecated

from .._protocols import SupportsProgress


class Module:
    """Some module with an expired function."""

    def __init__(self, expires = "never"):
        self.module = [
            b"from openfisca_core.commons import deprecated",
            b"",
            b"",
            f"@deprecated(since = 'today', expires = '{expires}')".encode(),
            b"def function() -> None:",
            b"    ..."
            ]

    def __enter__(self):
        self.file = tempfile.NamedTemporaryFile()
        self.name = ".".join(self.file.name.split("/")[-2:])
        self.file.write(b"\n".join(self.module))
        self.file.seek(0)
        return self.file, self.name

    def __exit__(self, *__):
        self.file.close()


@pytest.fixture
def progress():

    def name():
        return inspect.stack()[1][3]

    class Call(NamedTuple):
        name: str
        args: str = None

    class ProgressBar(SupportsProgress):

        def init(self):
            self.called = []

        def push(self, __count, __total):
            ...

        def warn(self, message):
            self.called.append(Call(name(), message))

        def fail(self):
            self.called.append(Call(name()))

        def wipe(self):
            ...

    return ProgressBar()


def test_find_deprecated(progress):
    """Prints out the features marked as deprecated."""

    with Module() as (file, name):
        checker = CheckDeprecated([file.name])
        checker(progress)

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit)

    assert exit.value.code == os.EX_OK
    assert progress.called[-1].name == "warn"
    assert f"{name}.function:5" in progress.called[-1].args


def test_find_deprecated_when_expired(progress):
    """Raises an error when at least one deprecation has expired."""

    version = "1.0.0"

    with Module(version) as (file, _):
        checker = CheckDeprecated([file.name], version)
        checker(progress)

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit)

    assert exit.value.code != os.EX_OK
    assert progress.called[-1].name == "fail"
