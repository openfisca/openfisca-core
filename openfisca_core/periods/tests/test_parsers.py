import pytest

from openfisca_core import periods
from openfisca_core.periods import DateUnit
from openfisca_core.periods import _helpers as parsers

year = DateUnit.YEAR


@pytest.mark.parametrize("arg, expected", [
    ["1", None],
    ["1000", None],
    ["1000-01", None],
    ["1000-01-01", None],
    ["1000-01-1", None],
    ["1000-01-99", None],
    ["1000-1", None],
    ["1000-1-1", None],
    ["999", None],
    ["eternity", None],
    ["first-of", None],
    ["year:2021:7", None],
    [(1, 1), None],
    [(1, 1, 1), None],
    [(1, 1, 1, 1), None],
    [(1,), None],
    [(2022, 1), None],
    [(2022, 1, 1), None],
    [(2022, 12), None],
    [(2022, 12, 1), None],
    [(2022, 12, 31), None],
    [(2022, 12, 32), None],
    [(2022, 13), None],
    [(2022, 13, 31), None],
    [(2022,), None],
    [1, (1, 1, 1, 4, 1)],
    [1., None],
    [1000, (1000, 1, 1, 4, 1)],
    [1000., None],
    [year, None],
    [{1, 1, 1, 1}, None],
    [{1, 1, 1}, None],
    [{1, 1}, None],
    [{1, }, None],
    ])
def test_parse_iso_format_from_int(arg, expected):
    """Returns an ``ISOFormat`` when given a valid ISO format int."""

    assert parsers.parse_int(arg) == expected


@pytest.mark.parametrize("arg, expected", [
    ["1", None],
    ["1000", None],
    ["1000-01", None],
    ["1000-01-01", None],
    ["1000-01-1", None],
    ["1000-01-99", None],
    ["1000-1", None],
    ["1000-1-1", None],
    ["999", None],
    ["eternity", None],
    ["first-of", None],
    ["year:2021:7", None],
    [(1, 1), (1, 1, 1, 2, 1)],
    [(1, 1, 1), (1, 1, 1, 1, 1)],
    [(1, 1, 1, 1), None],
    [(1,), (1, 1, 1, 4, 1)],
    [(2022, 1), (2022, 1, 1, 2, 1)],
    [(2022, 1, 1), (2022, 1, 1, 1, 1)],
    [(2022, 12), (2022, 12, 1, 2, 1)],
    [(2022, 12, 1), (2022, 12, 1, 1, 1)],
    [(2022, 12, 31), (2022, 12, 31, 1, 1)],
    [(2022, 12, 32), None],
    [(2022, 13), None],
    [(2022, 13, 31), None],
    [(2022,), (2022, 1, 1, 4, 1)],
    [1, None],
    [1., None],
    [1000, None],
    [1000., None],
    [year, None],
    [{1, 1, 1, 1}, None],
    [{1, 1, 1}, None],
    [{1, 1}, None],
    [{1}, None],
    ])
def test_parse_iso_format_from_seq(arg, expected):
    """Returns an ``ISOFormat`` when given a valid ISO format sequence."""

    assert parsers.parse_seq(arg) == expected


@pytest.mark.parametrize("arg, expected", [
    ["1", None],
    ["1000", (1000, 1, 1, 4, 1)],
    ["1000-01", (1000, 1, 1, 2, 1)],
    ["1000-01-01", (1000, 1, 1, 1, 1)],
    ["1000-01-1", None],
    ["1000-01-99", None],
    ["1000-1", None],
    ["1000-1-1", None],
    ["999", None],
    ["eternity", None],
    ["first-of", None],
    ["year:2021:7", (2021, 1, 1, 4, 7)],
    [(1, 1), None],
    [(1, 1, 1), None],
    [(1, 1, 1, 1), None],
    [(1,), None],
    [(2022, 1), None],
    [(2022, 1, 1), None],
    [(2022, 12), None],
    [(2022, 12, 1), None],
    [(2022, 12, 31), None],
    [(2022, 12, 32), None],
    [(2022, 13), None],
    [(2022, 13, 31), None],
    [(2022,), None],
    [1, None],
    [1., None],
    [1000, None],
    [1000., None],
    [year, None],
    [{1, 1, 1, 1}, None],
    [{1, 1, 1}, None],
    [{1, 1}, None],
    [{1, }, None],
    ])
def test_parse_iso_format_from_complex_str(arg, expected):
    """Returns an ``ISOFormat`` when given a valid complex period."""

    assert parsers.parse_period_str(arg) == expected


@pytest.mark.parametrize("arg, expected", [
    ["1", None],
    ["1000", (1000, 1, 1, 4, 1)],
    ["1000-01", (1000, 1, 1, 2, 1)],
    ["1000-01-01", (1000, 1, 1, 1, 1)],
    ["1000-01-1", None],
    ["1000-01-99", None],
    ["1000-1", None],
    ["1000-1-1", None],
    ["999", None],
    ["eternity", None],
    ["first-of", None],
    ["year:2021:7", None],
    [(1, 1), None],
    [(1, 1, 1), None],
    [(1, 1, 1, 1), None],
    [(1,), None],
    [(2022, 1), None],
    [(2022, 1, 1), None],
    [(2022, 12), None],
    [(2022, 12, 1), None],
    [(2022, 12, 31), None],
    [(2022, 12, 32), None],
    [(2022, 13), None],
    [(2022, 13, 31), None],
    [(2022,), None],
    [1, None],
    [1., None],
    [1000, None],
    [1000., None],
    [year, None],
    [{1, 1, 1, 1}, None],
    [{1, 1, 1}, None],
    [{1, 1}, None],
    [{1, }, None],
    ])
def test_parse_iso_format_from_str(arg, expected):
    """Returns an ``ISOFormat`` when given a valid ISO format string."""

    assert periods.parse(arg) == expected
