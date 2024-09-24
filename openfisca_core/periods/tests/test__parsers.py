import pytest
from pendulum.parsing import ParserError

from openfisca_core.periods import DateUnit, Instant, Period, _parsers


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
def test__parse_period(arg, expected) -> None:
    assert _parsers._parse_period(arg) == expected


@pytest.mark.parametrize(
    ("arg", "error"),
    [
        (None, AttributeError),
        ({}, AttributeError),
        ((), AttributeError),
        ([], AttributeError),
        (1, AttributeError),
        ("", AttributeError),
        ("à", ParserError),
        ("1", ValueError),
        ("-1", ValueError),
        ("999", ParserError),
        ("1000-0", ParserError),
        ("1000-1", ParserError),
        ("1000-1-1", ParserError),
        ("1000-00", ParserError),
        ("1000-13", ParserError),
        ("1000-01-00", ParserError),
        ("1000-01-99", ParserError),
        ("1000-W0", ParserError),
        ("1000-W1", ParserError),
        ("1000-W99", ParserError),
        ("1000-W1-0", ParserError),
        ("1000-W1-1", ParserError),
        ("1000-W1-99", ParserError),
        ("1000-W01-0", ParserError),
        ("1000-W01-00", ParserError),
    ],
)
def test__parse_period_with_invalid_argument(arg, error) -> None:
    with pytest.raises(error):
        _parsers._parse_period(arg)


@pytest.mark.parametrize(
    ("arg", "expected"),
    [
        ("2022", DateUnit.YEAR),
        ("2022-01", DateUnit.MONTH),
        ("2022-01-01", DateUnit.DAY),
        ("2022-W01", DateUnit.WEEK),
        ("2022-W01-01", DateUnit.WEEKDAY),
    ],
)
def test__parse_unit(arg, expected) -> None:
    assert _parsers._parse_unit(arg) == expected
