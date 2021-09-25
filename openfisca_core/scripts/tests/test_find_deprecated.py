import os
import sys

import pytest

from openfisca_core.commons import deprecated
from openfisca_core.scripts import FindDeprecated


@deprecated(since = "yesterday", expires = "1.0.0")
def function(a: int, b: float) -> float:
    return a + b


def test_find_deprecated(capsys):
    """Prints out the features marked as deprecated."""

    find = FindDeprecated()
    find()

    with pytest.raises(SystemExit) as exit:
        sys.exit(find.exit)

    assert exit.value.code == os.EX_OK
    assert "tests.test_find_deprecated.function:11" in capsys.readouterr().out


def test_find_deprecated_when_expired(capsys):
    """Raises an error when at least one deprecation has expired."""

    find = FindDeprecated("1.0.0")
    find()

    with pytest.raises(SystemExit) as exit:
        sys.exit(find.exit)

    assert exit.value.code != os.EX_OK
