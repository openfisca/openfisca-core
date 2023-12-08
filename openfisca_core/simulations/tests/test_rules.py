from openfisca_core.simulations.types import Variable

import pytest

from openfisca_core import commons, periods
from openfisca_core.simulations import _rules


class TestVariable(Variable):
    def __init__(self, name, definition_period):
        self.name = name
        self.definition_period = definition_period


def derive_calculate_add(state):
    either = (
        commons.either(state)
        .then(_rules._check_periods_compatibility_1)
        .then(_rules._check_periods_compatibility_2)
    )

    if either.is_success:
        return either.unwrap()

    raise ValueError(either.unwrap())


@pytest.mark.parametrize(
    "period_unit, period_str, expected",
    [
        (periods.YEAR, "2020", True),
        (periods.YEAR, "2020-01", True),
        (periods.YEAR, "2020-01-01", True),
        (periods.YEAR, "2020-W01", True),
        (periods.YEAR, "2020-W01-1", True),
        (periods.MONTH, "2020", True),
        (periods.MONTH, "2020-01", True),
        (periods.MONTH, "2020-01-01", True),
        (periods.MONTH, "2020-W01", False),
        (periods.MONTH, "2020-W01-1", True),
        (periods.DAY, "2020", True),
        (periods.DAY, "2020-01", True),
        (periods.DAY, "2020-01-01", True),
        (periods.DAY, "2020-W01", False),
        (periods.DAY, "2020-W01-1", True),
        (periods.WEEK, "2020", True),
        (periods.WEEK, "2020-01", True),
        (periods.WEEK, "2020-01-01", True),
        (periods.WEEK, "2020-W01", True),
        (periods.WEEK, "2020-W01-1", True),
        (periods.WEEKDAY, "2020", True),
        (periods.WEEKDAY, "2020-01", True),
        (periods.WEEKDAY, "2020-01-01", True),
        (periods.WEEKDAY, "2020-W01", True),
        (periods.WEEKDAY, "2020-W01-1", True),
    ],
)
def test_are_periods_compatible_1(period_unit, period_str, expected):
    variable = TestVariable("variable", period_unit)
    period = periods.period(period_str)
    either = _rules._check_periods_compatibility_1(
        {"variable": variable, "period": period}
    )
    assert either.is_success is expected


# @pytest.mark.parametrize(
#     "period_unit, period_str, expected",
#     [
#         (periods.YEAR, "2020", True),
#         (periods.YEAR, "2020-01", True),
#         (periods.YEAR, "2020-01-01", True),
#         (periods.YEAR, "2020-W01", True),
#         (periods.YEAR, "2020-W01-1", True),
#         (periods.MONTH, "2020", True),
#         (periods.MONTH, "2020-01", True),
#         (periods.MONTH, "2020-01-01", True),
#         (periods.MONTH, "2020-W01", True),
#         (periods.MONTH, "2020-W01-1", True),
#         (periods.DAY, "2020", True),
#         (periods.DAY, "2020-01", True),
#         (periods.DAY, "2020-01-01", True),
#         (periods.DAY, "2020-W01", True),
#         (periods.DAY, "2020-W01-1", True),
#         (periods.WEEK, "2020", True),
#         (periods.WEEK, "2020-01", False),
#         (periods.WEEK, "2020-01-01", True),
#         (periods.WEEK, "2020-W01", True),
#         (periods.WEEK, "2020-W01-1", True),
#         (periods.WEEKDAY, "2020", True),
#         (periods.WEEKDAY, "2020-01", False),
#         (periods.WEEKDAY, "2020-01-01", True),
#         (periods.WEEKDAY, "2020-W01", True),
#         (periods.WEEKDAY, "2020-W01-1", True),
#     ],
# )
# def test_are_periods_compatible_2(period_unit, period_str, expected):
#     variable = TestVariable("variable", period_unit)
#     period = periods.period(period_str)
#     either = _rules._check_periods_compatibility_2({variable: variable, period: period})
#     assert either.is_success is expected
#
#
# @pytest.mark.parametrize(
#     "period_unit, period_str",
#     [
#         (periods.YEAR, "2020"),
#         (periods.YEAR, "2020-01"),
#         (periods.YEAR, "2020-01-01"),
#         (periods.YEAR, "2020-W01"),
#         (periods.YEAR, "2020-W01-1"),
#         (periods.MONTH, "2020"),
#         (periods.MONTH, "2020-01"),
#         (periods.MONTH, "2020-01-01"),
#         (periods.MONTH, "2020-W01-1"),
#         (periods.DAY, "2020"),
#         (periods.DAY, "2020-01"),
#         (periods.DAY, "2020-01-01"),
#         (periods.DAY, "2020-W01-1"),
#         (periods.WEEK, "2020"),
#         (periods.WEEK, "2020-01-01"),
#         (periods.WEEK, "2020-W01"),
#         (periods.WEEK, "2020-W01-1"),
#         (periods.WEEKDAY, "2020"),
#         (periods.WEEKDAY, "2020-01-01"),
#         (periods.WEEKDAY, "2020-W01"),
#         (periods.WEEKDAY, "2020-W01-1"),
#     ],
# )
# def test_derive_calculate_add(period_unit, period_str):
#     variable = TestVariable("variable", period_unit)
#     period = periods.period(period_str)
#     assert derive_calculate_add({variable: variable, period: period})
#
#
# @pytest.mark.parametrize(
#     "period_unit, period_str",
#     [
#         (periods.MONTH, "2020-W01"),
#         (periods.DAY, "2020-W01"),
#     ],
# )
# def test_derive_calculate_add_with_invalid_period_1(period_unit, period_str):
#     variable = TestVariable("variable", period_unit)
#     period = periods.period(period_str)
#     with pytest.raises(ValueError) as error:
#         derive_calculate_add({variable: variable, period: period})
#     assert "period.first_week" not in str(error.value)
#
#
# @pytest.mark.parametrize(
#     "period_unit, period_str",
#     [
#         (periods.WEEK, "2020-01"),
#         (periods.WEEKDAY, "2020-01"),
#     ],
# )
# def test_derive_calculate_add_with_invalid_period_2(period_unit, period_str):
#     variable = TestVariable("variable", period_unit)
#     period = periods.period(period_str)
#     with pytest.raises(ValueError) as error:
#         derive_calculate_add({variable: variable, period: period})
#     assert "period.first_week" in str(error.value)
