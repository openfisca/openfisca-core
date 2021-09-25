import os
import sys
import tempfile

import pytest

from openfisca_tasks import CheckDeprecated


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


def test_find_deprecated(capsys):
    """Prints out the features marked as deprecated."""

    with Module() as (file, name):
        checker = CheckDeprecated([file.name])
        checker()

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit)

    assert exit.value.code == os.EX_OK
    assert f"[i] {name}.function:5" in capsys.readouterr().out


def test_find_deprecated_when_expired(capsys):
    """Raises an error when at least one deprecation has expired."""

    version = "1.0.0"

    with Module(version) as (file, _):
        checker = CheckDeprecated([file.name], version)
        checker()

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit)

    assert exit.value.code != os.EX_OK
    assert "[!]" in capsys.readouterr().out
