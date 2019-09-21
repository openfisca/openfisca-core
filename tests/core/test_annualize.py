import numpy as np
from pytest import fixture

from openfisca_core import periods
from openfisca_core.model_api import *  # noqa analysis:ignore
from openfisca_country_template.entities import Household, Person
from openfisca_core.reforms import annualize


@fixture
def monthly_variable():
    class monthly_variable(Variable):
        value_type = int
        entity = Person
        definition_period = MONTH
        nof_call = 0

        def formula(person, period, parameters):
            monthly_variable.nof_call += 1
            return np.asarray([100])


    variable = monthly_variable()

    return variable


class PopulationMock:
    # Simulate a population for whom a variable has already been put in cache for January.

    def __init__(self, variable):
        self.variable = variable

    def __call__(self, variable_name, period):
        if period.start.month == 1:
            return np.asarray([100])
        else:
            return self.variable.get_formula(period)(self, period, None)


def test_without_annualize(monthly_variable):
    period = periods.period(2019)

    person = PopulationMock(monthly_variable)

    yearly_sum = sum(
        person('monthly_variable', month)
        for month in period.get_subperiods(MONTH)
    )

    assert monthly_variable.nof_call == 11
    assert yearly_sum == 1200


def test_with_annualize(monthly_variable):
    period = periods.period(2019)
    annualized_variable = annualize(monthly_variable)

    person = PopulationMock(annualized_variable)

    yearly_sum = sum(
        person('monthly_variable', month)
        for month in period.get_subperiods(MONTH)
    )

    assert monthly_variable.nof_call == 0
    assert yearly_sum == 100 * 12

def test_with_partial_annualize(monthly_variable):
    period = periods.period('year:2018:2')
    annualized_variable = annualize(monthly_variable, periods.period(2018))

    person = PopulationMock(annualized_variable)

    yearly_sum = sum(
        person('monthly_variable', month)
        for month in period.get_subperiods(MONTH)
    )

    assert monthly_variable.nof_call == 11
    assert yearly_sum == 100 * 12 * 2
