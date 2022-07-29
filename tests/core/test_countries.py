import pytest

from openfisca_core import periods, populations, tools
from openfisca_core.errors import VariableNameConflictError, VariableNotFoundError
from openfisca_core.periods import DateUnit
from openfisca_core.simulations import SimulationBuilder
from openfisca_core.variables import Variable

PERIOD = periods.period("2016-01")


@pytest.mark.parametrize("simulation", [({"salary": 2000}, PERIOD)], indirect = True)
def test_input_variable(simulation):
    result = simulation.calculate("salary", PERIOD)
    tools.assert_near(result, [2000], absolute_error_margin = 0.01)


@pytest.mark.parametrize("simulation", [({"salary": 2000}, PERIOD)], indirect = True)
def test_basic_calculation(simulation):
    result = simulation.calculate("income_tax", PERIOD)
    tools.assert_near(result, [300], absolute_error_margin = 0.01)


@pytest.mark.parametrize("simulation", [({"salary": 24000}, PERIOD)], indirect = True)
def test_calculate_add(simulation):
    result = simulation.calculate_add("income_tax", PERIOD)
    tools.assert_near(result, [3600], absolute_error_margin = 0.01)


@pytest.mark.parametrize(
    "simulation",
    [({"accommodation_size": 100, "housing_occupancy_status": "tenant"}, PERIOD)],
    indirect = True,
    )
def test_calculate_divide(simulation):
    result = simulation.calculate_divide("housing_tax", PERIOD)
    tools.assert_near(result, [1000 / 12.], absolute_error_margin = 0.01)


@pytest.mark.parametrize("simulation", [({"salary": 20000}, PERIOD)], indirect = True)
def test_bareme(simulation):
    result = simulation.calculate("social_security_contribution", PERIOD)
    expected = [0.02 * 6000 + 0.06 * 6400 + 0.12 * 7600]
    tools.assert_near(result, expected, absolute_error_margin = 0.01)


@pytest.mark.parametrize("simulation", [({}, PERIOD)], indirect = True)
def test_non_existing_variable(simulation):
    with pytest.raises(VariableNotFoundError):
        simulation.calculate("non_existent_variable", PERIOD)


@pytest.mark.parametrize("simulation", [({}, PERIOD)], indirect = True)
def test_calculate_variable_with_wrong_definition_period(simulation):
    year = str(PERIOD.this_year)

    with pytest.raises(ValueError) as error:
        simulation.calculate("basic_income", year)

    error_message = str(error.value)
    expected_words = ["period", year, "month", "basic_income", "ADD"]

    for word in expected_words:
        assert word in error_message, f"Expected '{word}' in error message '{error_message}'"


@pytest.mark.parametrize("simulation", [({}, PERIOD)], indirect = True)
def test_divide_option_on_month_defined_variable(simulation):
    with pytest.raises(ValueError):
        simulation.person("disposable_income", PERIOD, options = [populations.DIVIDE])


@pytest.mark.parametrize("simulation", [({}, PERIOD)], indirect = True)
def test_divide_option_with_complex_period(simulation):
    quarter = PERIOD.last_3_months

    with pytest.raises(ValueError) as error:
        simulation.household("housing_tax", quarter, options = [populations.DIVIDE])

    error_message = str(error.value)
    expected_words = ["DIVIDE", "one-year", "one-month", "period"]

    for word in expected_words:
        assert word in error_message, f"Expected '{word}' in error message '{error_message}'"


def test_input_with_wrong_period(tax_benefit_system):
    year = str(PERIOD.this_year)
    variables = {"basic_income": {year: 12000}}
    simulation_builder = SimulationBuilder()
    simulation_builder.set_default_period(PERIOD)

    with pytest.raises(ValueError):
        simulation_builder.build_from_variables(tax_benefit_system, variables)


def test_variable_with_reference(make_simulation, isolated_tax_benefit_system):
    variables = {"salary": 4000}
    simulation = make_simulation(isolated_tax_benefit_system, variables, PERIOD)

    result = simulation.calculate("disposable_income", PERIOD)

    assert result > 0

    class disposable_income(Variable):
        definition_period = DateUnit.MONTH

        def formula(household, period):
            return household.empty_array()

    isolated_tax_benefit_system.update_variable(disposable_income)
    simulation = make_simulation(isolated_tax_benefit_system, variables, PERIOD)

    result = simulation.calculate("disposable_income", PERIOD)

    assert result == 0


def test_variable_name_conflict(tax_benefit_system):

    class disposable_income(Variable):
        reference = "disposable_income"
        definition_period = DateUnit.MONTH

        def formula(household, period):
            return household.empty_array()

    with pytest.raises(VariableNameConflictError):
        tax_benefit_system.add_variable(disposable_income)
