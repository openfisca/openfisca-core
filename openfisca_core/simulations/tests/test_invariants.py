from typing import TypedDict

from openfisca_core.simulations.types import Variable

import enum

import pytest

from openfisca_core import periods


class EitherTag(enum.Enum):
    FAILURE = enum.auto()
    SUCCESS = enum.auto()


class Either:
    def __init__(self, value, tag=EitherTag.SUCCESS):
        self._value = value
        self._tag = tag

    @property
    def isSuccess(self):
        return self._tag == EitherTag.SUCCESS

    @property
    def isFailure(self):
        return self._tag == EitherTag.FAILURE

    def map(self, f):
        if self.isSuccess:
            return Either.succeed(f(**self.unwrap()))

        return self

    def join(self):
        if self.isSuccess and isinstance(self.unwrap(), Either):
            return self.unwrap()

        return self

    def then(self, f):
        return self.map(f).join()

    def unwrap(self):
        return self._value

    @staticmethod
    def fail(value):
        return Either(value, EitherTag.FAILURE)

    @staticmethod
    def succeed(value):
        return Either(value, EitherTag.SUCCESS)


class TestVariable(Variable):
    def __init__(self, name, definition_period):
        self.name = name
        self.definition_period = definition_period


class ValidationParams(TypedDict):
    variable: Variable
    period: periods.Period


def are_periods_compatible_1(**params):
    variable = params["variable"]
    period = params["period"]

    if (
        variable.definition_period in (periods.MONTH, periods.DAY)
        and period.unit == periods.WEEK
    ):
        return Either.fail(
            f"Unable to compute variable '{variable.name}' for period "
            f"{period}, as {period} and {variable.definition_period} are "
            "incompatible periods. You can, however, change the requested "
            "period to 'period.this_year'."
        )

    return Either.succeed(params)


def are_periods_compatible_2(**params):
    variable = params["variable"]
    period = params["period"]

    if (
        variable.definition_period in (periods.WEEK, periods.WEEKDAY)
        and period.unit == periods.MONTH
    ):
        return Either.fail(
            f"Unable to compute variable '{variable.name}' for period "
            f"{period}, as {period} and {variable.definition_period} are "
            "incompatible periods. You can, however, change the requested "
            "period to 'period.this_year' or 'period.first_week'."
        )

    return Either.succeed(params)


def derive_calculate_add(**params):
    either = (
        Either(params).then(are_periods_compatible_1).then(are_periods_compatible_2)
    )

    if either.isSuccess:
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
    either = are_periods_compatible_1(variable=variable, period=period)
    assert either.isSuccess is expected


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
        (periods.MONTH, "2020-W01", True),
        (periods.MONTH, "2020-W01-1", True),
        (periods.DAY, "2020", True),
        (periods.DAY, "2020-01", True),
        (periods.DAY, "2020-01-01", True),
        (periods.DAY, "2020-W01", True),
        (periods.DAY, "2020-W01-1", True),
        (periods.WEEK, "2020", True),
        (periods.WEEK, "2020-01", False),
        (periods.WEEK, "2020-01-01", True),
        (periods.WEEK, "2020-W01", True),
        (periods.WEEK, "2020-W01-1", True),
        (periods.WEEKDAY, "2020", True),
        (periods.WEEKDAY, "2020-01", False),
        (periods.WEEKDAY, "2020-01-01", True),
        (periods.WEEKDAY, "2020-W01", True),
        (periods.WEEKDAY, "2020-W01-1", True),
    ],
)
def test_are_periods_compatible_2(period_unit, period_str, expected):
    variable = TestVariable("variable", period_unit)
    period = periods.period(period_str)
    either = are_periods_compatible_2(variable=variable, period=period)
    assert either.isSuccess is expected


@pytest.mark.parametrize(
    "period_unit, period_str",
    [
        (periods.YEAR, "2020"),
        (periods.YEAR, "2020-01"),
        (periods.YEAR, "2020-01-01"),
        (periods.YEAR, "2020-W01"),
        (periods.YEAR, "2020-W01-1"),
        (periods.MONTH, "2020"),
        (periods.MONTH, "2020-01"),
        (periods.MONTH, "2020-01-01"),
        (periods.MONTH, "2020-W01-1"),
        (periods.DAY, "2020"),
        (periods.DAY, "2020-01"),
        (periods.DAY, "2020-01-01"),
        (periods.DAY, "2020-W01-1"),
        (periods.WEEK, "2020"),
        (periods.WEEK, "2020-01-01"),
        (periods.WEEK, "2020-W01"),
        (periods.WEEK, "2020-W01-1"),
        (periods.WEEKDAY, "2020"),
        (periods.WEEKDAY, "2020-01-01"),
        (periods.WEEKDAY, "2020-W01"),
        (periods.WEEKDAY, "2020-W01-1"),
    ],
)
def test_derive_calculate_add(period_unit, period_str):
    variable = TestVariable("variable", period_unit)
    period = periods.period(period_str)
    assert derive_calculate_add(variable=variable, period=period)


@pytest.mark.parametrize(
    "period_unit, period_str",
    [
        (periods.MONTH, "2020-W01"),
        (periods.DAY, "2020-W01"),
    ],
)
def test_derive_calculate_add_with_invalid_period_1(period_unit, period_str):
    variable = TestVariable("variable", period_unit)
    period = periods.period(period_str)
    with pytest.raises(ValueError) as error:
        derive_calculate_add(variable=variable, period=period)
    assert "period.first_week" not in str(error.value)


@pytest.mark.parametrize(
    "period_unit, period_str",
    [
        (periods.WEEK, "2020-01"),
        (periods.WEEKDAY, "2020-01"),
    ],
)
def test_derive_calculate_add_with_invalid_period_2(period_unit, period_str):
    variable = TestVariable("variable", period_unit)
    period = periods.period(period_str)
    with pytest.raises(ValueError) as error:
        derive_calculate_add(variable=variable, period=period)
    assert "period.first_week" in str(error.value)
