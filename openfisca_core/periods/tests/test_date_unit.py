import pytest

from openfisca_core.periods import DateUnit


@pytest.mark.parametrize("operation", [
    "DAY" in DateUnit,
    "day" in DateUnit,
    2 in DateUnit,
    "DAY" == DateUnit.DAY,
    "day" == DateUnit.DAY,
    2 == DateUnit.DAY,
    "DAY" < DateUnit.MONTH,
    "day" < DateUnit.MONTH,
    2 < DateUnit.MONTH,
    "MONTH" > DateUnit.DAY,
    "month" > DateUnit.DAY,
    3 > DateUnit.DAY,
    "DAY" <= DateUnit.DAY,
    "day" <= DateUnit.DAY,
    2 <= DateUnit.DAY,
    "DAY" >= DateUnit.DAY,
    "day" >= DateUnit.DAY,
    2 >= DateUnit.DAY,
    ])
def test_date_unit(operation):
    """It works! :)"""

    assert operation


@pytest.mark.parametrize("operation", [
    "DAY" in DateUnit.isoformat,
    "day" in DateUnit.isoformat,
    2 in DateUnit.isoformat,
    ])
def test_isoformat(operation):
    """It works! :)"""

    assert operation


@pytest.mark.parametrize("operation", [
    "WEEK" in DateUnit.isocalendar,
    "week" in DateUnit.isocalendar,
    1 in DateUnit.isocalendar,
    ])
def test_isocalendar(operation):
    """It works! :)"""

    assert operation