import pytest

from openfisca_core import entities, holders, periods, populations, tools, variables


@pytest.fixture
def people():
    return entities.Entity(
        key="person",
        plural="people",
        label="An individual member of a larger group.",
        doc="People have the particularity of not being someone else.",
    )


@pytest.fixture
def Income(people):
    return type(
        "Income",
        (variables.Variable,),
        {"value_type": float, "entity": people},
    )


@pytest.fixture
def population(people):
    population = populations.Population(people)
    population.count = 1
    return population


@pytest.mark.parametrize(
    "dispatch_unit, definition_unit, values, expected",
    [
        [periods.DateUnit.YEAR, periods.DateUnit.YEAR, [1.0], [3.0]],
        [periods.DateUnit.YEAR, periods.DateUnit.MONTH, [1.0], [36.0]],
        [periods.DateUnit.YEAR, periods.DateUnit.DAY, [1.0], [1096.0]],
        [periods.DateUnit.YEAR, periods.DateUnit.WEEK, [1.0], [157.0]],
        [periods.DateUnit.YEAR, periods.DateUnit.WEEKDAY, [1.0], [1096.0]],
        [periods.DateUnit.MONTH, periods.DateUnit.YEAR, [1.0], [1.0]],
        [periods.DateUnit.MONTH, periods.DateUnit.MONTH, [1.0], [3.0]],
        [periods.DateUnit.MONTH, periods.DateUnit.DAY, [1.0], [90.0]],
        [periods.DateUnit.MONTH, periods.DateUnit.WEEK, [1.0], [13.0]],
        [periods.DateUnit.MONTH, periods.DateUnit.WEEKDAY, [1.0], [90.0]],
        [periods.DateUnit.DAY, periods.DateUnit.YEAR, [1.0], [1.0]],
        [periods.DateUnit.DAY, periods.DateUnit.MONTH, [1.0], [1.0]],
        [periods.DateUnit.DAY, periods.DateUnit.DAY, [1.0], [3.0]],
        [periods.DateUnit.DAY, periods.DateUnit.WEEK, [1.0], [1.0]],
        [periods.DateUnit.DAY, periods.DateUnit.WEEKDAY, [1.0], [3.0]],
        [periods.DateUnit.WEEK, periods.DateUnit.YEAR, [1.0], [1.0]],
        [periods.DateUnit.WEEK, periods.DateUnit.MONTH, [1.0], [1.0]],
        [periods.DateUnit.WEEK, periods.DateUnit.DAY, [1.0], [21.0]],
        [periods.DateUnit.WEEK, periods.DateUnit.WEEK, [1.0], [3.0]],
        [periods.DateUnit.WEEK, periods.DateUnit.WEEKDAY, [1.0], [21.0]],
        [periods.DateUnit.WEEK, periods.DateUnit.YEAR, [1.0], [1.0]],
        [periods.DateUnit.WEEK, periods.DateUnit.MONTH, [1.0], [1.0]],
        [periods.DateUnit.WEEK, periods.DateUnit.DAY, [1.0], [21.0]],
        [periods.DateUnit.WEEK, periods.DateUnit.WEEK, [1.0], [3.0]],
        [periods.DateUnit.WEEK, periods.DateUnit.WEEKDAY, [1.0], [21.0]],
        [periods.DateUnit.WEEKDAY, periods.DateUnit.YEAR, [1.0], [1.0]],
        [periods.DateUnit.WEEKDAY, periods.DateUnit.MONTH, [1.0], [1.0]],
        [periods.DateUnit.WEEKDAY, periods.DateUnit.DAY, [1.0], [3.0]],
        [periods.DateUnit.WEEKDAY, periods.DateUnit.WEEK, [1.0], [1.0]],
        [periods.DateUnit.WEEKDAY, periods.DateUnit.WEEKDAY, [1.0], [3.0]],
    ],
)
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
    holder = holders.Holder(income, population)
    instant = periods.Instant((2022, 1, 1))
    dispatch_period = periods.Period((dispatch_unit, instant, 3))

    holders.set_input_dispatch_by_period(holder, dispatch_period, values)
    total = sum(map(holder.get_array, holder.get_known_periods()))

    tools.assert_near(total, expected, absolute_error_margin=0.001)


@pytest.mark.parametrize(
    "divide_unit, definition_unit, values, expected",
    [
        [periods.DateUnit.YEAR, periods.DateUnit.YEAR, [3.0], [1.0]],
        [periods.DateUnit.YEAR, periods.DateUnit.MONTH, [36.0], [1.0]],
        [periods.DateUnit.YEAR, periods.DateUnit.DAY, [1095.0], [1.0]],
        [periods.DateUnit.YEAR, periods.DateUnit.WEEK, [157.0], [1.0]],
        [periods.DateUnit.YEAR, periods.DateUnit.WEEKDAY, [1095.0], [1.0]],
        [periods.DateUnit.MONTH, periods.DateUnit.YEAR, [1.0], [1.0]],
        [periods.DateUnit.MONTH, periods.DateUnit.MONTH, [3.0], [1.0]],
        [periods.DateUnit.MONTH, periods.DateUnit.DAY, [90.0], [1.0]],
        [periods.DateUnit.MONTH, periods.DateUnit.WEEK, [13.0], [1.0]],
        [periods.DateUnit.MONTH, periods.DateUnit.WEEKDAY, [90.0], [1.0]],
        [periods.DateUnit.DAY, periods.DateUnit.YEAR, [1.0], [1.0]],
        [periods.DateUnit.DAY, periods.DateUnit.MONTH, [1.0], [1.0]],
        [periods.DateUnit.DAY, periods.DateUnit.DAY, [3.0], [1.0]],
        [periods.DateUnit.DAY, periods.DateUnit.WEEK, [1.0], [1.0]],
        [periods.DateUnit.DAY, periods.DateUnit.WEEKDAY, [3.0], [1.0]],
        [periods.DateUnit.WEEK, periods.DateUnit.YEAR, [1.0], [1.0]],
        [periods.DateUnit.WEEK, periods.DateUnit.MONTH, [1.0], [1.0]],
        [periods.DateUnit.WEEK, periods.DateUnit.DAY, [21.0], [1.0]],
        [periods.DateUnit.WEEK, periods.DateUnit.WEEK, [3.0], [1.0]],
        [periods.DateUnit.WEEK, periods.DateUnit.WEEKDAY, [21.0], [1.0]],
        [periods.DateUnit.WEEKDAY, periods.DateUnit.YEAR, [1.0], [1.0]],
        [periods.DateUnit.WEEKDAY, periods.DateUnit.MONTH, [1.0], [1.0]],
        [periods.DateUnit.WEEKDAY, periods.DateUnit.DAY, [3.0], [1.0]],
        [periods.DateUnit.WEEKDAY, periods.DateUnit.WEEK, [1.0], [1.0]],
        [periods.DateUnit.WEEKDAY, periods.DateUnit.WEEKDAY, [3.0], [1.0]],
    ],
)
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
    holder = holders.Holder(income, population)
    instant = periods.Instant((2022, 1, 1))
    divide_period = periods.Period((divide_unit, instant, 3))

    holders.set_input_divide_by_period(holder, divide_period, values)
    last = holder.get_array(holder.get_known_periods()[-1])

    tools.assert_near(last, expected, absolute_error_margin=0.001)
