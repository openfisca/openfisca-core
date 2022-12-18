import pytest

from openfisca_core.periods import ISOFormat


@pytest.mark.parametrize("arg, expected", [
    ["1", None],
    ["1000", (4, 1000, 1, 1, 1)],
    ["1000-01", (2, 1000, 1, 1, 2)],
    ["1000-01-01", (1, 1000, 1, 1, 3)],
    ["1000-01-1", None],
    ["1000-01-99", None],
    ["1000-1", None],
    ["1000-1-1", None],
    ["999", None],
    ])
def test_parse_iso_format(arg, expected):
    """Returns an ``ISOFormat`` when given a valid ISO format string."""

    assert ISOFormat.parse(arg) == expected
