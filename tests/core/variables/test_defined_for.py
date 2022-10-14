import numpy as np
from policyengine_core.simulations import SimulationBuilder
from policyengine_core.taxbenefitsystems import TaxBenefitSystem
from policyengine_core.model_api import *
from policyengine_core.entities import Entity


def test_defined_for_no_deps():
    """A basic test of the defined-for logic, on a variable with no dependencies."""
    Person = Entity("person", "people", "Person", "A person")
    system = TaxBenefitSystem([Person])

    class in_england(Variable):
        value_type = bool
        entity = Person
        definition_period = ETERNITY
        label = "In England"

    class income(Variable):
        value_type = float
        entity = Person
        definition_period = ETERNITY
        label = "Income"
        defined_for = "in_england"

        def formula(person, period, parameters):
            return 1

    system.add_variables(in_england, income)

    simulation = SimulationBuilder().build_from_dict(
        system,
        {
            "people": {
                "first_person": {
                    "in_england": {2022: True},
                },
                "second_person": {
                    "in_england": {2022: False},
                },
            },
        },
    )

    assert all(simulation.calculate("income", 2022) == np.array([1, 0]))


def test_defined_for_with_deps():
    """An intermediate test of the defined-for logic, on a variable with one dependent variable."""
    Person = Entity("person", "people", "Person", "A person")
    system = TaxBenefitSystem([Person])

    class in_england(Variable):
        value_type = bool
        entity = Person
        definition_period = ETERNITY
        label = "In England"

    class tax(Variable):
        value_type = float
        entity = Person
        definition_period = ETERNITY
        label = "Tax"

        def formula(person, period, parameters):
            return 0.5

    class income(Variable):
        value_type = float
        entity = Person
        definition_period = ETERNITY
        label = "Income"
        defined_for = "in_england"

        def formula(person, period, parameters):
            tax = person("tax", period)
            return 1 - tax

    system.add_variables(in_england, income, tax)

    simulation = SimulationBuilder().build_from_dict(
        system,
        {
            "people": {
                "first_person": {
                    "in_england": {2022: True},
                },
                "second_person": {
                    "in_england": {2022: False},
                },
            },
        },
    )

    assert all(simulation.calculate("income", 2022) == np.array([0.5, 0]))


test_defined_for_with_deps()
