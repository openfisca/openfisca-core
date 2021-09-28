import numpy
import pytest

from openfisca_country_template.entities import Person

from openfisca_core import periods, variables
from openfisca_core.variables import Variable


@pytest.fixture
def monthly_variable():

    calculation_count = 0

    class monthly_variable(Variable):
        calculation_count: int
        value_type = int
        entity = Person
        definition_period = periods.MONTH

        def formula(person, _period, _parameters):  # pylint: disable=no-self-use
            variable.calculation_count += 1
            return numpy.asarray([100])

    variable = monthly_variable()
    variable.calculation_count = calculation_count

    return variable


class PopulationMock:
    # Simulate a population for whom a variable has already been put in cache for January.

    def __init__(self, variable):
        self.variable = variable

    def __call__(self, variable_name, period):
        if period.start.month == 1:
            return numpy.asarray([100])

        return self.variable.get_formula(period)(self, period, None)


def test_without_annualize(monthly_variable):
    period = periods.period(2019)

    person = PopulationMock(monthly_variable)

    yearly_sum = sum(
        person('monthly_variable', month)
        for month in period.get_subperiods(periods.MONTH)
        )

    assert monthly_variable.calculation_count == 11
    assert yearly_sum == 1200


def test_with_annualize(monthly_variable):
    period = periods.period(2019)
    annualized_variable = variables.get_annualized_variable(monthly_variable)

    person = PopulationMock(annualized_variable)

    yearly_sum = sum(
        person('monthly_variable', month)
        for month in period.get_subperiods(periods.MONTH)
        )

    assert monthly_variable.calculation_count == 0
    assert yearly_sum == 100 * 12


def test_with_partial_annualize(monthly_variable):
    period = periods.period('year:2018:2')
    annualized_variable = variables.get_annualized_variable(monthly_variable, periods.period(2018))

    person = PopulationMock(annualized_variable)

    yearly_sum = sum(
        person('monthly_variable', month)
        for month in period.get_subperiods(periods.MONTH)
        )

    assert monthly_variable.calculation_count == 11
    assert yearly_sum == 100 * 12 * 2
