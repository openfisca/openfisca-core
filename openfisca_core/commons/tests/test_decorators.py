import re

import pytest

from openfisca_core.commons import deprecated


def test_deprecated():
    """The decorated function throws a deprecation warning when used."""

    since = "yesterday"
    expires = "doomsday"
    match = re.compile(f"^.*{since}.*{expires}.*$")

    @deprecated(since, expires)
    def function(a: int, b: float) -> float:
        return a + b

    with pytest.warns(DeprecationWarning, match = match):
        assert function(1, 2.) == 3.
