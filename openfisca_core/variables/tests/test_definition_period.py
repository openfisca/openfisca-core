import pytest

from openfisca_core import periods
from openfisca_core.variables import Variable


@pytest.fixture
def variable(persons):
    class TestVariable(Variable):
        value_type = float
        entity = persons

    return TestVariable


def test_weekday_variable(variable) -> None:
    variable.definition_period = periods.WEEKDAY
    assert variable()


def test_week_variable(variable) -> None:
    variable.definition_period = periods.WEEK
    assert variable()


def test_day_variable(variable) -> None:
    variable.definition_period = periods.DAY
    assert variable()


def test_month_variable(variable) -> None:
    variable.definition_period = periods.MONTH
    assert variable()


def test_year_variable(variable) -> None:
    variable.definition_period = periods.YEAR
    assert variable()


def test_eternity_variable(variable) -> None:
    variable.definition_period = periods.ETERNITY
    assert variable()
