import pytest

from openfisca_core.periods import DateUnit, Instant, Period, _parsers


@pytest.mark.parametrize("arg, expected", [
    ["", None],
    ["1", Period((DateUnit.YEAR, Instant((1, 1, 1)), 1))],
    ["-1", None],
    ["999", Period((DateUnit.YEAR, Instant((999, 1, 1)), 1))],
    ["1000", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 1))],
    ["1000-0", None],
    ["1000-1", Period((DateUnit.MONTH, Instant((1000, 1, 1)), 1))],
    ["1000-01", Period((DateUnit.MONTH, Instant((1000, 1, 1)), 1))],
    ["1000-12", Period((DateUnit.MONTH, Instant((1000, 12, 1)), 1))],
    ["1000-13", None],
    ["1000-W0", None],
    ["1000-W1", None],
    ["1000-W52", None],
    ["1000-W99", None],
    ["1000-1-1", Period((DateUnit.DAY, Instant((1000, 1, 1)), 1))],
    ["1000-01-1", Period((DateUnit.DAY, Instant((1000, 1, 1)), 1))],
    ["1000-01-01", Period((DateUnit.DAY, Instant((1000, 1, 1)), 1))],
    ["1000-W1-1", None],
    ["1000-01-99", None],
    ["1000-W1-99", None],
    ])
def test__from_isoformat_period(arg, expected):
    assert _parsers._from_isoformat(arg) == expected

@pytest.mark.parametrize("arg, error", [
    [None, AttributeError],
    [{}, AttributeError],
    [(), AttributeError],
    [[], AttributeError],
    [1, AttributeError],
    ])
def test__from_isoformat_with_invalid_argument(arg, error):
    with pytest.raises(error):
        _parsers._from_isoformat(arg)


@pytest.mark.parametrize("arg, expected", [
    ["", None],
    ["1", None],
    ["-1", None],
    ["999", None],
    ["1000", None],
    ["1000-0", None],
    ["1000-1", None],
    ["1000-01", None],
    ["1000-W0", None],
    ["1000-W1", Period((DateUnit.WEEK, Instant((999, 12, 30)), 1))],
    ["1000-W52", Period((DateUnit.WEEK, Instant((1000, 12, 22)), 1))],
    ["1000-W99", None],
    ["1000-1-1", None],
    ["1000-01-1", None],
    ["1000-01-01", None],
    ["1000-W1-1", Period((DateUnit.WEEKDAY, Instant((999, 12, 30)), 1))],
    ["1000-01-99", None],
    ["1000-W1-99", None],
    ])
def test__from_isocalendar(arg, expected):
    assert _parsers._from_isocalendar(arg) == expected


@pytest.mark.parametrize("arg, error", [
    [None, AttributeError],
    [{}, AttributeError],
    [(), AttributeError],
    [[], AttributeError],
    [1, AttributeError],
    ])
def test__from_isocalendar_with_invalid_argument(arg, error):
    with pytest.raises(error):
        _parsers._from_isocalendar(arg)
