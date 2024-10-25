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
        key="person",
        plural="people",
        label="An individual member of a larger group.",
        doc="People have the particularity of not being someone else.",
    )


@pytest.fixture
def Income(people):
    return type(
        "Income",
        (Variable,),
        {"value_type": float, "entity": people},
    )


@pytest.fixture
def population(people):
    population = Population(people)
    population.count = 1
    return population


@pytest.mark.parametrize(
    ("dispatch_unit", "definition_unit", "values", "expected"),
    [
        (DateUnit.YEAR, DateUnit.YEAR, [1.0], [3.0]),
        (DateUnit.YEAR, DateUnit.MONTH, [1.0], [36.0]),
        (DateUnit.YEAR, DateUnit.DAY, [1.0], [1096.0]),
        (DateUnit.YEAR, DateUnit.WEEK, [1.0], [157.0]),
        (DateUnit.YEAR, DateUnit.WEEKDAY, [1.0], [1096.0]),
        (DateUnit.MONTH, DateUnit.YEAR, [1.0], [1.0]),
        (DateUnit.MONTH, DateUnit.MONTH, [1.0], [3.0]),
        (DateUnit.MONTH, DateUnit.DAY, [1.0], [90.0]),
        (DateUnit.MONTH, DateUnit.WEEK, [1.0], [13.0]),
        (DateUnit.MONTH, DateUnit.WEEKDAY, [1.0], [90.0]),
        (DateUnit.DAY, DateUnit.YEAR, [1.0], [1.0]),
        (DateUnit.DAY, DateUnit.MONTH, [1.0], [1.0]),
        (DateUnit.DAY, DateUnit.DAY, [1.0], [3.0]),
        (DateUnit.DAY, DateUnit.WEEK, [1.0], [1.0]),
        (DateUnit.DAY, DateUnit.WEEKDAY, [1.0], [3.0]),
        (DateUnit.WEEK, DateUnit.YEAR, [1.0], [1.0]),
        (DateUnit.WEEK, DateUnit.MONTH, [1.0], [1.0]),
        (DateUnit.WEEK, DateUnit.DAY, [1.0], [21.0]),
        (DateUnit.WEEK, DateUnit.WEEK, [1.0], [3.0]),
        (DateUnit.WEEK, DateUnit.WEEKDAY, [1.0], [21.0]),
        (DateUnit.WEEKDAY, DateUnit.YEAR, [1.0], [1.0]),
        (DateUnit.WEEKDAY, DateUnit.MONTH, [1.0], [1.0]),
        (DateUnit.WEEKDAY, DateUnit.DAY, [1.0], [3.0]),
        (DateUnit.WEEKDAY, DateUnit.WEEK, [1.0], [1.0]),
        (DateUnit.WEEKDAY, DateUnit.WEEKDAY, [1.0], [3.0]),
    ],
)
def test_set_input_dispatch_by_period(
    Income,
    population,
    dispatch_unit,
    definition_unit,
    values,
    expected,
) -> None:
    Income.definition_period = definition_unit
    income = Income()
    holder = Holder(income, population)
    instant = Instant((2022, 1, 1))
    dispatch_period = Period((dispatch_unit, instant, 3))

    holders.set_input_dispatch_by_period(holder, dispatch_period, values)
    total = sum(map(holder.get_array, holder.get_known_periods()))

    tools.assert_near(total, expected, absolute_error_margin=0.001)


@pytest.mark.parametrize(
    ("divide_unit", "definition_unit", "values", "expected"),
    [
        (DateUnit.YEAR, DateUnit.YEAR, [3.0], [1.0]),
        (DateUnit.YEAR, DateUnit.MONTH, [36.0], [1.0]),
        (DateUnit.YEAR, DateUnit.DAY, [1095.0], [1.0]),
        (DateUnit.YEAR, DateUnit.WEEK, [157.0], [1.0]),
        (DateUnit.YEAR, DateUnit.WEEKDAY, [1095.0], [1.0]),
        (DateUnit.MONTH, DateUnit.YEAR, [1.0], [1.0]),
        (DateUnit.MONTH, DateUnit.MONTH, [3.0], [1.0]),
        (DateUnit.MONTH, DateUnit.DAY, [90.0], [1.0]),
        (DateUnit.MONTH, DateUnit.WEEK, [13.0], [1.0]),
        (DateUnit.MONTH, DateUnit.WEEKDAY, [90.0], [1.0]),
        (DateUnit.DAY, DateUnit.YEAR, [1.0], [1.0]),
        (DateUnit.DAY, DateUnit.MONTH, [1.0], [1.0]),
        (DateUnit.DAY, DateUnit.DAY, [3.0], [1.0]),
        (DateUnit.DAY, DateUnit.WEEK, [1.0], [1.0]),
        (DateUnit.DAY, DateUnit.WEEKDAY, [3.0], [1.0]),
        (DateUnit.WEEK, DateUnit.YEAR, [1.0], [1.0]),
        (DateUnit.WEEK, DateUnit.MONTH, [1.0], [1.0]),
        (DateUnit.WEEK, DateUnit.DAY, [21.0], [1.0]),
        (DateUnit.WEEK, DateUnit.WEEK, [3.0], [1.0]),
        (DateUnit.WEEK, DateUnit.WEEKDAY, [21.0], [1.0]),
        (DateUnit.WEEKDAY, DateUnit.YEAR, [1.0], [1.0]),
        (DateUnit.WEEKDAY, DateUnit.MONTH, [1.0], [1.0]),
        (DateUnit.WEEKDAY, DateUnit.DAY, [3.0], [1.0]),
        (DateUnit.WEEKDAY, DateUnit.WEEK, [1.0], [1.0]),
        (DateUnit.WEEKDAY, DateUnit.WEEKDAY, [3.0], [1.0]),
    ],
)
def test_set_input_divide_by_period(
    Income,
    population,
    divide_unit,
    definition_unit,
    values,
    expected,
) -> None:
    Income.definition_period = definition_unit
    income = Income()
    holder = Holder(income, population)
    instant = Instant((2022, 1, 1))
    divide_period = Period((divide_unit, instant, 3))

    holders.set_input_divide_by_period(holder, divide_period, values)
    last = holder.get_array(holder.get_known_periods()[-1])

    tools.assert_near(last, expected, absolute_error_margin=0.001)
