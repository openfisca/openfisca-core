import re

import pytest

from openfisca_core import commons


def test_deprecated():
    """The decorated function throws a deprecation warning when used."""

    since = "yesterday"
    expires = "doomsday"
    match = re.compile(f"^.*function.*{since}.*{expires}.*$")

    @commons.deprecated(since, expires)
    def function(a: int, b: float) -> float:
        return a + b

    with pytest.warns(DeprecationWarning, match = match):
        assert function(1, 2.) == 3.
