import warnings

import pytest

from policyengine_core import periods
from policyengine_core.country_template.entities import Household, Person
from policyengine_core.model_api import *
from policyengine_core.parameters import ParameterNode
from policyengine_core.periods import Instant
from policyengine_core.tools import assert_near


class goes_to_school(Variable):
    value_type = bool
    default_value = True
    entity = Person
    label = "The person goes to school (only relevant for children)"
    definition_period = MONTH


class WithBasicIncomeNeutralized(Reform):
    def apply(self):
        self.neutralize_variable("basic_income")


@pytest.fixture(scope="module", autouse=True)
def add_variables_to_tax_benefit_system(tax_benefit_system):
    tax_benefit_system.add_variables(goes_to_school)


def test_formula_neutralization(make_simulation, tax_benefit_system):
    reform = WithBasicIncomeNeutralized(tax_benefit_system)

    period = "2017-01"
    simulation = make_simulation(reform.base_tax_benefit_system, {}, period)
    simulation.debug = True

    basic_income = simulation.calculate("basic_income", period=period)
    assert_near(basic_income, 600)
    disposable_income = simulation.calculate(
        "disposable_income", period=period
    )
    assert disposable_income > 0

    reform_simulation = make_simulation(reform, {}, period)
    reform_simulation.debug = True

    basic_income_reform = reform_simulation.calculate(
        "basic_income", period="2013-01"
    )
    assert_near(basic_income_reform, 0, absolute_error_margin=0)
    disposable_income_reform = reform_simulation.calculate(
        "disposable_income", period=period
    )
    assert_near(disposable_income_reform, 0)


def test_neutralization_variable_with_default_value(
    make_simulation, tax_benefit_system
):
    class test_goes_to_school_neutralization(Reform):
        def apply(self):
            self.neutralize_variable("goes_to_school")

    reform = test_goes_to_school_neutralization(tax_benefit_system)

    period = "2017-01"
    simulation = make_simulation(reform.base_tax_benefit_system, {}, period)

    goes_to_school = simulation.calculate("goes_to_school", period)
    assert_near(goes_to_school, [True], absolute_error_margin=0)


def test_neutralization_optimization(make_simulation, tax_benefit_system):
    reform = WithBasicIncomeNeutralized(tax_benefit_system)

    period = "2017-01"
    simulation = make_simulation(reform, {}, period)
    simulation.debug = True

    simulation.calculate("basic_income", period="2013-01")
    simulation.calculate_add("basic_income", period="2013")

    # As basic_income is neutralized, it should not be cached
    basic_income_holder = simulation.persons.get_holder("basic_income")
    assert basic_income_holder.get_known_periods() == []


def test_input_variable_neutralization(make_simulation, tax_benefit_system):
    class test_salary_neutralization(Reform):
        def apply(self):
            self.neutralize_variable("salary")

    reform = test_salary_neutralization(tax_benefit_system)

    period = "2017-01"

    reform = test_salary_neutralization(tax_benefit_system)

    with warnings.catch_warnings(record=True) as raised_warnings:
        reform_simulation = make_simulation(
            reform, {"salary": [1200, 1000]}, period
        )
        assert (
            "You cannot set a value for the variable"
            in raised_warnings[0].message.args[0]
        )
    salary = reform_simulation.calculate("salary", period)
    assert_near(
        salary,
        [0, 0],
    )
    disposable_income_reform = reform_simulation.calculate(
        "disposable_income", period=period
    )
    assert_near(disposable_income_reform, [600, 600])


def test_permanent_variable_neutralization(
    make_simulation, tax_benefit_system
):
    class test_date_naissance_neutralization(Reform):
        def apply(self):
            self.neutralize_variable("birth")

    reform = test_date_naissance_neutralization(tax_benefit_system)

    period = "2017-01"
    simulation = make_simulation(
        reform.base_tax_benefit_system, {"birth": "1980-01-01"}, period
    )
    with warnings.catch_warnings(record=True) as raised_warnings:
        reform_simulation = make_simulation(
            reform, {"birth": "1980-01-01"}, period
        )
        assert (
            "You cannot set a value for the variable"
            in raised_warnings[0].message.args[0]
        )
    assert str(simulation.calculate("birth", None)[0]) == "1980-01-01"
    assert str(reform_simulation.calculate("birth", None)[0]) == "1970-01-01"


def test_add_variable(make_simulation, tax_benefit_system):
    class new_variable(Variable):
        value_type = int
        label = "Nouvelle variable introduite par la réforme"
        entity = Household
        definition_period = MONTH

        def formula(household, period):
            return household.empty_array() + 10

    class test_add_variable(Reform):
        def apply(self):
            self.add_variable(new_variable)

    reform = test_add_variable(tax_benefit_system)

    assert tax_benefit_system.get_variable("new_variable") is None
    reform_simulation = make_simulation(reform, {}, 2013)
    reform_simulation.debug = True
    new_variable1 = reform_simulation.calculate(
        "new_variable", period="2013-01"
    )
    assert_near(new_variable1, 10, absolute_error_margin=0)


def test_add_dated_variable(make_simulation, tax_benefit_system):
    class new_dated_variable(Variable):
        value_type = int
        label = "Nouvelle variable introduite par la réforme"
        entity = Household
        definition_period = MONTH

        def formula_2010_01_01(household, period):
            return household.empty_array() + 10

        def formula_2011_01_01(household, period):
            return household.empty_array() + 15

    class test_add_variable(Reform):
        def apply(self):
            self.add_variable(new_dated_variable)

    reform = test_add_variable(tax_benefit_system)

    reform_simulation = make_simulation(reform, {}, "2013-01")
    reform_simulation.debug = True
    new_dated_variable1 = reform_simulation.calculate(
        "new_dated_variable", period="2013-01"
    )
    assert_near(new_dated_variable1, 15, absolute_error_margin=0)


def test_update_variable(make_simulation, tax_benefit_system):
    class disposable_income(Variable):
        definition_period = MONTH

        def formula_2018(household, period):
            return household.empty_array() + 10

    class test_update_variable(Reform):
        def apply(self):
            self.update_variable(disposable_income)

    reform = test_update_variable(tax_benefit_system)

    disposable_income_reform = reform.get_variable("disposable_income")
    disposable_income_baseline = tax_benefit_system.get_variable(
        "disposable_income"
    )

    assert disposable_income_reform is not None
    assert (
        disposable_income_reform.entity.plural
        == disposable_income_baseline.entity.plural
    )
    assert disposable_income_reform.name == disposable_income_baseline.name
    assert disposable_income_reform.label == disposable_income_baseline.label

    reform_simulation = make_simulation(reform, {}, 2018)
    disposable_income1 = reform_simulation.calculate(
        "disposable_income", period="2018-01"
    )
    assert_near(disposable_income1, 10, absolute_error_margin=0)

    disposable_income2 = reform_simulation.calculate(
        "disposable_income", period="2017-01"
    )
    # Before 2018, the former formula is used
    assert disposable_income2 > 100


def test_replace_variable(tax_benefit_system):
    class disposable_income(Variable):
        definition_period = MONTH
        entity = Person
        label = "Disposable income"
        value_type = float

        def formula_2018(household, period):
            return household.empty_array() + 10

    class test_update_variable(Reform):
        def apply(self):
            self.replace_variable(disposable_income)

    reform = test_update_variable(tax_benefit_system)

    disposable_income_reform = reform.get_variable("disposable_income")
    assert disposable_income_reform.get_formula("2017") is None


def test_wrong_reform(tax_benefit_system):
    class wrong_reform(Reform):
        # A Reform must implement an `apply` method
        pass

    with pytest.raises(Exception):
        wrong_reform(tax_benefit_system)


def test_modify_parameters(tax_benefit_system):
    def modify_parameters(reference_parameters):
        reform_parameters_subtree = ParameterNode(
            "new_node",
            data={
                "new_param": {
                    "values": {
                        "2000-01-01": {"value": True},
                        "2015-01-01": {"value": None},
                    }
                },
            },
        )
        reference_parameters.children["new_node"] = reform_parameters_subtree
        return reference_parameters

    class test_modify_parameters(Reform):
        def apply(self):
            self.modify_parameters(modifier_function=modify_parameters)

    reform = test_modify_parameters(tax_benefit_system)

    parameters_new_node = reform.parameters.children["new_node"]
    assert parameters_new_node is not None

    instant = Instant((2013, 1, 1))
    parameters_at_instant = reform.get_parameters_at_instant(instant)
    assert parameters_at_instant.new_node.new_param is True


def test_attributes_conservation(tax_benefit_system):
    class some_variable(Variable):
        value_type = int
        entity = Person
        label = "Variable with many attributes"
        definition_period = MONTH
        set_input = set_input_divide_by_period
        calculate_output = calculate_output_add

    tax_benefit_system.add_variable(some_variable)

    class reform(Reform):
        class some_variable(Variable):
            default_value = 10

        def apply(self):
            self.update_variable(some_variable)

    reformed_tbs = reform(tax_benefit_system)
    reform_variable = reformed_tbs.get_variable("some_variable")
    baseline_variable = tax_benefit_system.get_variable("some_variable")
    assert reform_variable.value_type == baseline_variable.value_type
    assert reform_variable.entity == baseline_variable.entity
    assert reform_variable.label == baseline_variable.label
    assert (
        reform_variable.definition_period
        == baseline_variable.definition_period
    )
    assert reform_variable.set_input == baseline_variable.set_input
    assert (
        reform_variable.calculate_output == baseline_variable.calculate_output
    )


def test_formulas_removal(tax_benefit_system):
    class reform(Reform):
        def apply(self):
            class basic_income(Variable):
                pass

            self.update_variable(basic_income)
            self.variables["basic_income"].formulas.clear()

    reformed_tbs = reform(tax_benefit_system)
    reform_variable = reformed_tbs.get_variable("basic_income")
    baseline_variable = tax_benefit_system.get_variable("basic_income")
    assert len(reform_variable.formulas) == 0
    assert len(baseline_variable.formulas) > 0
