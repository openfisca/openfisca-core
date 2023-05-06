import pytest

from openfisca_core import holders, tools
from openfisca_core.entities import Entity
from openfisca_core.holders import Holder
from openfisca_core.periods import DateUnit, Instant, Period
from openfisca_core.populations import Population
from openfisca_core.variables import Variable


@pytest.fixture
def people():
    return Entity(
        key = "person",
        plural = "people",
        label = "An individual member of a larger group.",
        doc = "People have the particularity of not being someone else.",
        )


@pytest.fixture
def Income(people):
    return type(
        "Income",
        (Variable,), {
            "value_type": float,
            "entity": people
            },
        )


@pytest.fixture
def population(people):
    population = Population(people)
    population.count = 1
    return population


@pytest.mark.parametrize("dispatch_unit, definition_unit, values, expected", [
    [DateUnit.YEAR, DateUnit.YEAR, [1.], [3.]],
    [DateUnit.YEAR, DateUnit.MONTH, [1.], [36.]],
    [DateUnit.YEAR, DateUnit.DAY, [1.], [1096.]],
    [DateUnit.YEAR, DateUnit.WEEK, [1.], [157.]],
    [DateUnit.YEAR, DateUnit.WEEKDAY, [1.], [1096.]],
    [DateUnit.MONTH, DateUnit.YEAR, [1.], [1.]],
    [DateUnit.MONTH, DateUnit.MONTH, [1.], [3.]],
    [DateUnit.MONTH, DateUnit.DAY, [1.], [90.]],
    [DateUnit.MONTH, DateUnit.WEEK, [1.], [13.]],
    [DateUnit.MONTH, DateUnit.WEEKDAY, [1.], [90.]],
    [DateUnit.DAY, DateUnit.YEAR, [1.], [1.]],
    [DateUnit.DAY, DateUnit.MONTH, [1.], [1.]],
    [DateUnit.DAY, DateUnit.DAY, [1.], [3.]],
    [DateUnit.DAY, DateUnit.WEEK, [1.], [1.]],
    [DateUnit.DAY, DateUnit.WEEKDAY, [1.], [3.]],
    [DateUnit.WEEK, DateUnit.YEAR, [1.], [1.]],
    [DateUnit.WEEK, DateUnit.MONTH, [1.], [1.]],
    [DateUnit.WEEK, DateUnit.DAY, [1.], [21.]],
    [DateUnit.WEEK, DateUnit.WEEK, [1.], [3.]],
    [DateUnit.WEEK, DateUnit.WEEKDAY, [1.], [21.]],
    [DateUnit.WEEK, DateUnit.YEAR, [1.], [1.]],
    [DateUnit.WEEK, DateUnit.MONTH, [1.], [1.]],
    [DateUnit.WEEK, DateUnit.DAY, [1.], [21.]],
    [DateUnit.WEEK, DateUnit.WEEK, [1.], [3.]],
    [DateUnit.WEEK, DateUnit.WEEKDAY, [1.], [21.]],
    [DateUnit.WEEKDAY, DateUnit.YEAR, [1.], [1.]],
    [DateUnit.WEEKDAY, DateUnit.MONTH, [1.], [1.]],
    [DateUnit.WEEKDAY, DateUnit.DAY, [1.], [3.]],
    [DateUnit.WEEKDAY, DateUnit.WEEK, [1.], [1.]],
    [DateUnit.WEEKDAY, DateUnit.WEEKDAY, [1.], [3.]],
    ])
def test_set_input_dispatch_by_period(
        Income,
        population,
        dispatch_unit,
        definition_unit,
        values,
        expected,
        ):
    Income.definition_period = definition_unit
    income = Income()
    holder = Holder(income, population)
    instant = Instant((2022, 1, 1))
    dispatch_period = Period((dispatch_unit, instant, 3))

    holders.set_input_dispatch_by_period(holder, dispatch_period, values)
    total = sum(map(holder.get_array, holder.get_known_periods()))

    tools.assert_near(total, expected, absolute_error_margin = 0.001)


@pytest.mark.parametrize("divide_unit, definition_unit, values, expected", [
    [DateUnit.YEAR, DateUnit.YEAR, [3.], [1.]],
    [DateUnit.YEAR, DateUnit.MONTH, [36.], [1.]],
    [DateUnit.YEAR, DateUnit.DAY, [1095.], [1.]],
    [DateUnit.YEAR, DateUnit.WEEK, [157.], [1.]],
    [DateUnit.YEAR, DateUnit.WEEKDAY, [1095.], [1.]],
    [DateUnit.MONTH, DateUnit.YEAR, [1.], [1.]],
    [DateUnit.MONTH, DateUnit.MONTH, [3.], [1.]],
    [DateUnit.MONTH, DateUnit.DAY, [90.], [1.]],
    [DateUnit.MONTH, DateUnit.WEEK, [13.], [1.]],
    [DateUnit.MONTH, DateUnit.WEEKDAY, [90.], [1.]],
    [DateUnit.DAY, DateUnit.YEAR, [1.], [1.]],
    [DateUnit.DAY, DateUnit.MONTH, [1.], [1.]],
    [DateUnit.DAY, DateUnit.DAY, [3.], [1.]],
    [DateUnit.DAY, DateUnit.WEEK, [1.], [1.]],
    [DateUnit.DAY, DateUnit.WEEKDAY, [3.], [1.]],
    [DateUnit.WEEK, DateUnit.YEAR, [1.], [1.]],
    [DateUnit.WEEK, DateUnit.MONTH, [1.], [1.]],
    [DateUnit.WEEK, DateUnit.DAY, [21.], [1.]],
    [DateUnit.WEEK, DateUnit.WEEK, [3.], [1.]],
    [DateUnit.WEEK, DateUnit.WEEKDAY, [21.], [1.]],
    [DateUnit.WEEKDAY, DateUnit.YEAR, [1.], [1.]],
    [DateUnit.WEEKDAY, DateUnit.MONTH, [1.], [1.]],
    [DateUnit.WEEKDAY, DateUnit.DAY, [3.], [1.]],
    [DateUnit.WEEKDAY, DateUnit.WEEK, [1.], [1.]],
    [DateUnit.WEEKDAY, DateUnit.WEEKDAY, [3.], [1.]],
    ])
def test_set_input_divide_by_period(
        Income,
        population,
        divide_unit,
        definition_unit,
        values,
        expected,
        ):
    Income.definition_period = definition_unit
    income = Income()
    holder = Holder(income, population)
    instant = Instant((2022, 1, 1))
    divide_period = Period((divide_unit, instant, 3))

    holders.set_input_divide_by_period(holder, divide_period, values)
    last = holder.get_array(holder.get_known_periods()[-1])

    tools.assert_near(last, expected, absolute_error_margin = 0.001)
