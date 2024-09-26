import pytest

from openfisca_core.periods import (
    DateUnit,
    Instant,
    InstantError,
    ParserError,
    Period,
    PeriodError,
    _parsers,
)


@pytest.mark.parametrize(
    ("arg", "expected"),
    [
        ("1001", Instant((1001, 1, 1))),
        ("1001-01", Instant((1001, 1, 1))),
        ("1001-12", Instant((1001, 12, 1))),
        ("1001-01-01", Instant((1001, 1, 1))),
        ("2028-02-29", Instant((2028, 2, 29))),
        ("1001-W01", Instant((1000, 12, 29))),
        ("1001-W52", Instant((1001, 12, 21))),
        ("1001-W01-1", Instant((1000, 12, 29))),
    ],
)
def test_parse_instant(arg, expected) -> None:
    assert _parsers.parse_instant(arg) == expected


@pytest.mark.parametrize(
    ("arg", "error"),
    [
        (None, InstantError),
        ({}, InstantError),
        ((), InstantError),
        ([], InstantError),
        (1, InstantError),
        ("", InstantError),
        ("à", InstantError),
        ("1", InstantError),
        ("-1", InstantError),
        ("999", InstantError),
        ("1000-0", InstantError),
        ("1000-1", ParserError),
        ("1000-1-1", InstantError),
        ("1000-00", InstantError),
        ("1000-13", InstantError),
        ("1000-01-00", InstantError),
        ("1000-01-99", InstantError),
        ("2029-02-29", ParserError),
        ("1000-W0", InstantError),
        ("1000-W1", InstantError),
        ("1000-W99", InstantError),
        ("1000-W1-0", InstantError),
        ("1000-W1-1", InstantError),
        ("1000-W1-99", InstantError),
        ("1000-W01-0", InstantError),
        ("1000-W01-00", InstantError),
    ],
)
def test_parse_instant_with_invalid_argument(arg, error) -> None:
    with pytest.raises(error):
        _parsers.parse_instant(arg)


@pytest.mark.parametrize(
    ("arg", "expected"),
    [
        ("1001", Period((DateUnit.YEAR, Instant((1001, 1, 1)), 1))),
        ("1001-01", Period((DateUnit.MONTH, Instant((1001, 1, 1)), 1))),
        ("1001-12", Period((DateUnit.MONTH, Instant((1001, 12, 1)), 1))),
        ("1001-01-01", Period((DateUnit.DAY, Instant((1001, 1, 1)), 1))),
        ("1001-W01", Period((DateUnit.WEEK, Instant((1000, 12, 29)), 1))),
        ("1001-W52", Period((DateUnit.WEEK, Instant((1001, 12, 21)), 1))),
        ("1001-W01-1", Period((DateUnit.WEEKDAY, Instant((1000, 12, 29)), 1))),
    ],
)
def test_parse_period(arg, expected) -> None:
    assert _parsers.parse_period(arg) == expected


@pytest.mark.parametrize(
    ("arg", "error"),
    [
        (None, PeriodError),
        ({}, PeriodError),
        ((), PeriodError),
        ([], PeriodError),
        (1, PeriodError),
        ("", PeriodError),
        ("à", PeriodError),
        ("1", PeriodError),
        ("-1", PeriodError),
        ("999", PeriodError),
        ("1000-0", PeriodError),
        ("1000-1", ParserError),
        ("1000-1-1", PeriodError),
        ("1000-00", PeriodError),
        ("1000-13", PeriodError),
        ("1000-01-00", PeriodError),
        ("1000-01-99", PeriodError),
        ("1000-W0", PeriodError),
        ("1000-W1", PeriodError),
        ("1000-W99", PeriodError),
        ("1000-W1-0", PeriodError),
        ("1000-W1-1", PeriodError),
        ("1000-W1-99", PeriodError),
        ("1000-W01-0", PeriodError),
        ("1000-W01-00", PeriodError),
    ],
)
def test_parse_period_with_invalid_argument(arg, error) -> None:
    with pytest.raises(error):
        _parsers.parse_period(arg)


@pytest.mark.parametrize(
    ("arg", "expected"),
    [
        ("2022", DateUnit.YEAR),
        ("2022-01", DateUnit.MONTH),
        ("2022-01-01", DateUnit.DAY),
        ("2022-W01", DateUnit.WEEK),
        ("2022-W01-1", DateUnit.WEEKDAY),
    ],
)
def test_parse_unit(arg, expected) -> None:
    assert _parsers.parse_unit(arg) == expected
