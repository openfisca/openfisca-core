import pytest

from openfisca_core import holders, periods, tools
from openfisca_core.entities import Entity
from openfisca_core.holders import Holder
from openfisca_core.periods import Instant, Period
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
    [periods.DateUnit.YEAR, periods.DateUnit.YEAR, [1.], [3.]],
    [periods.DateUnit.YEAR, periods.DateUnit.MONTH, [1.], [36.]],
    [periods.DateUnit.YEAR, periods.DateUnit.DAY, [1.], [1096.]],
    [periods.DateUnit.MONTH, periods.DateUnit.YEAR, [1.], [1.]],
    [periods.DateUnit.MONTH, periods.DateUnit.MONTH, [1.], [3.]],
    [periods.DateUnit.MONTH, periods.DateUnit.DAY, [1.], [90.]],
    [periods.DateUnit.DAY, periods.DateUnit.YEAR, [1.], [1.]],
    [periods.DateUnit.DAY, periods.DateUnit.MONTH, [1.], [1.]],
    [periods.DateUnit.DAY, periods.DateUnit.DAY, [1.], [3.]],
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
    [periods.DateUnit.YEAR, periods.DateUnit.YEAR, [3.], [1.]],
    [periods.DateUnit.YEAR, periods.DateUnit.MONTH, [36.], [1.]],
    [periods.DateUnit.YEAR, periods.DateUnit.DAY, [1095.], [1.]],
    [periods.DateUnit.MONTH, periods.DateUnit.YEAR, [1.], [1.]],
    [periods.DateUnit.MONTH, periods.DateUnit.MONTH, [3.], [1.]],
    [periods.DateUnit.MONTH, periods.DateUnit.DAY, [90.], [1.]],
    [periods.DateUnit.DAY, periods.DateUnit.YEAR, [1.], [1.]],
    [periods.DateUnit.DAY, periods.DateUnit.MONTH, [1.], [1.]],
    [periods.DateUnit.DAY, periods.DateUnit.DAY, [3.], [1.]],
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
