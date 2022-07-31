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


def test_set_input_dispatch_by_period(
        Income,
        population,
        three_years,
        ):
    """Yearly income propagates evenly to the following years."""

    Income.definition_period = periods.MONTH
    income = Income()
    holder = Holder(income, population)
    values = [1000.]

    holders.set_input_dispatch_by_period(holder, three_years, values)

    known_periods = holder.get_known_periods()
    period_count = len(known_periods)

    assert period_count == 36  # Three years in months
    assert sum(map(holder.get_array, known_periods)) == [36000.]
