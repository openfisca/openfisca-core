import pytest

from openfisca_core.periods import DateUnit, ISOFormat


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
    [DateUnit.YEAR, None],
    [{1, 1, 1, 1}, None],
    [{1, 1, 1}, None],
    [{1, 1}, None],
    [{1, }, None],
    ])
def test_parse_iso_format_from_int(arg, expected):
    """Returns an ``ISOFormat`` when given a valid ISO format int."""

    assert ISOFormat.fromint(arg) == expected


@pytest.mark.parametrize("arg, expected", [
    ["1", None],
    ["1000", (1000, 1, 1, 4, 1)],
    ["1000-01", (1000, 1, 1, 2, 2)],
    ["1000-01-01", (1000, 1, 1, 1, 3)],
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
    [DateUnit.YEAR, None],
    [{1, 1, 1, 1}, None],
    [{1, 1, 1}, None],
    [{1, 1}, None],
    [{1, }, None],
    ])
def test_parse_iso_format_from_str(arg, expected):
    """Returns an ``ISOFormat`` when given a valid ISO format string."""

    assert ISOFormat.fromstr(arg) == expected


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
    [(1, 1), (1, 1, 1, 2, 2)],
    [(1, 1, 1), (1, 1, 1, 1, 3)],
    [(1, 1, 1, 1), None],
    [(1,), (1, 1, 1, 4, 1)],
    [(2022, 1), (2022, 1, 1, 2, 2)],
    [(2022, 1, 1), (2022, 1, 1, 1, 3)],
    [(2022, 12), (2022, 12, 1, 2, 2)],
    [(2022, 12, 1), (2022, 12, 1, 1, 3)],
    [(2022, 12, 31), (2022, 12, 31, 1, 3)],
    [(2022, 12, 32), None],
    [(2022, 13), None],
    [(2022, 13, 31), None],
    [(2022,), (2022, 1, 1, 4, 1)],
    [1, None],
    [1., None],
    [1000, None],
    [1000., None],
    [DateUnit.YEAR, None],
    [{1, 1, 1, 1}, None],
    [{1, 1, 1}, None],
    [{1, 1}, None],
    [{1}, None],
    ])
def test_parse_iso_format_from_seq(arg, expected):
    """Returns an ``ISOFormat`` when given a valid ISO format sequence."""

    assert ISOFormat.fromseq(arg) == expected
