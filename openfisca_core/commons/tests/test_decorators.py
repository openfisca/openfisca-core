import re

import pytest

from openfisca_core.commons import deprecated


def test_deprecated():
    """The decorated function throws a deprecation warning when used."""

    since = "yesterday"
    expires = "tomorrow"
    message = re.compile(f"^.*{since}.*{expires}.*$")

    @deprecated(since = since, expires = expires)
    def function(a: int, b: float) -> float:
        return a + b

    with pytest.warns(DeprecationWarning, match = message):
        assert function(1, 2.) == 3.


def test_deprecated_when_illegal():
    """Raises an error when the deprecation expiration is not a major."""

    since = "yesterday"
    expires = "1.2.3"
    message = "Deprecations can only expire on major releases"

    with pytest.raises(ValueError, match = message):
        deprecated(since = since, expires = expires)
