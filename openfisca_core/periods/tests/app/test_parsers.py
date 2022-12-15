import pytest

from openfisca_core import periods


@pytest.mark.parametrize("arg, expected", [
    ["1", None],
    ["1000", periods.Period((periods.DateUnit.YEAR, periods.Instant((1000, 1, 1)), 1))],
    ["1000-01", periods.Period((periods.DateUnit.MONTH, periods.Instant((1000, 1, 1)), 1))],
    ["1000-01-01", periods.Period((periods.DateUnit.DAY, periods.Instant((1000, 1, 1)), 1))],
    ["1000-01-1", None],
    ["1000-01-99", None],
    ["1000-1", None],
    ["1000-1-1", None],
    ["999", None],
    ])
def test_parse_period(arg, expected):
    """Returns an ``Instant`` when given a valid ISO format string."""

    assert periods.parse_period(arg) == expected
