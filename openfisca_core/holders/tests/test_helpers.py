import numpy
import pytest

from openfisca_core import holders, periods
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


@pytest.fixture
def beggining_of_year():
    return Instant((2022, 1, 1))


@pytest.fixture
def three_years(beggining_of_year):
    return Period((periods.YEAR, beggining_of_year, 3))


@pytest.fixture
def three_months(beggining_of_year):
    return Period((periods.MONTH, beggining_of_year, 3))


@pytest.fixture
def three_days(beggining_of_year):
    return Period((periods.DAY, beggining_of_year, 3))


@pytest.mark.parametrize("definition_period, values, expected", [
    [periods.YEAR, [43800.], [43800. * 3]],
    [periods.MONTH, [3650.], [3650. * 12 * 3]],
    # [periods.DAY, [120.], [131400.]],
    ])
def test_set_input_dispatch_by_period_over_3_years(
        Income,
        definition_period,
        population,
        three_years,
        values,
        expected,
        ):
    Income.definition_period = definition_period
    income = Income()
    holder = Holder(income, population)

    holders.set_input_dispatch_by_period(holder, three_years, values)

    assert sum(map(holder.get_array, holder.get_known_periods())) == expected


@pytest.mark.parametrize("definition_period, values, expected", [
    [periods.YEAR, [43800.], [43800.]],
    [periods.MONTH, [3650.], [3650. * 3]],
    # [periods.DAY, [120.], [131400.]],
    ])
def test_set_input_dispatch_by_period_over_3_months(
        Income,
        definition_period,
        population,
        three_months,
        values,
        expected,
        ):
    Income.definition_period = definition_period
    income = Income()
    holder = Holder(income, population)

    holders.set_input_dispatch_by_period(holder, three_months, values)

    assert sum(map(holder.get_array, holder.get_known_periods())) == expected


@pytest.mark.parametrize("definition_period, values, expected", [
    [periods.YEAR, [43800.], [43800.]],
    [periods.MONTH, [3650.], [3650.]],
    # [periods.DAY, [120.], [131400.]],
    ])
def test_set_input_dispatch_by_period_over_3_days(
        Income,
        definition_period,
        population,
        three_days,
        values,
        expected,
        ):
    Income.definition_period = definition_period
    income = Income()
    holder = Holder(income, population)

    holders.set_input_dispatch_by_period(holder, three_days, values)

    assert sum(map(holder.get_array, holder.get_known_periods())) == expected
