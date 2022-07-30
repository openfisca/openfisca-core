import pytest

from openfisca_core import periods
from openfisca_core.periods import Instant, Period, helpers


@pytest.mark.parametrize("arg, expected", [
    ["1", None],
    ["999", None],
    ["1000", Period((periods.YEAR, Instant((1000, 1, 1)), 1))],
    ["1000-1", Period((periods.MONTH, Instant((1000, 1, 1)), 1))],
    ["1000-01", Period((periods.MONTH, Instant((1000, 1, 1)), 1))],
    ["1000-1-1", Period((periods.DAY, Instant((1000, 1, 1)), 1))],
    ["1000-01-1", Period((periods.DAY, Instant((1000, 1, 1)), 1))],
    ["1000-01-01", Period((periods.DAY, Instant((1000, 1, 1)), 1))],
    ["1000-01-99", None],
    ])
def test__parse_simple_period_with_a_valid_argument(arg, expected):
    assert helpers._parse_simple_period(arg) == expected
