import numpy
import pytest

from openfisca_core.entities import Entity
from openfisca_core.periods import DateUnit
from openfisca_core.simulations.simulation_builder import SimulationBuilder
from openfisca_core.taxbenefitsystems import TaxBenefitSystem
from openfisca_core.variables import Variable


@pytest.fixture
def multimembers_entities():
    employee = Entity(key="employee", plural="employees", label="A employee")
    expense = Entity(key="expense", plural="expenses", label="An expense")
    contract = Entity(key="contract", plural="contracts", label="A contract")
    firm = Entity(key="firm", plural="firms", label="A firm")
    firm.add_relationship(
        employee,
        [
            {
                "key": "employee",
                "plural": "employees",
                "label": "Employee",
            },
        ],
    )
    firm.add_relationship(
        expense,
        [
            {
                "key": "expense",
                "plural": "expenses",
                "label": "Expense",
            },
        ],
    )
    firm.add_relationship(
        contract,
        [
            {
                "key": "contract",
                "plural": "contracts",
                "label": "Contract",
            },
        ],
    )
    return [employee, expense, contract, firm]


def test_has_multiple_members(multimembers_entities) -> None:
    system = TaxBenefitSystem(multimembers_entities)
    payload = {
        "employees": {"employee1": {}, "employee2": {}, "employee3": {}},
        "expenses": {
            "expense1": {"amount": {"ETERNITY": 100}},
            "expense2": {"amount": {"ETERNITY": 50}},
            "expense3": {"amount": {"ETERNITY": 25}},
        },
        "contracts": {
            "contract1": {
                "value": {"ETERNITY": 100},
            },
        },
        "firms": {
            "firm1": {
                "employees": ["employee1", "employee2"],
                "expenses": ["expense1", "expense3"],
                "contracts": ["contract1"],
            },
            "firm2": {
                "contracts": [],
                "expenses": ["expense2"],
            },
            "firm3": {
                "employees": ["employee3"],
                "contracts": [],
            },
        },
    }

    [_employee, expense, contract, firm] = multimembers_entities

    class amount(Variable):
        value_type = float
        entity = expense
        definition_period = DateUnit.ETERNITY

    class value(Variable):
        value_type = float
        entity = contract
        definition_period = DateUnit.ETERNITY

    class contribution(Variable):
        value_type = float
        entity = firm
        definition_period = DateUnit.ETERNITY

        def formula(firm, period):
            nb = firm.employees.membership.nb_members()

            # end goal
            # amounts = firm.expenses.sum("amount", period)
            # values = firm.contracts.sum("value", period)

            amounts_i = firm.expenses("amount", period)
            amounts = firm.expenses.membership.sum(amounts_i)
            values_i = firm.contracts("value", period)
            values = firm.contracts.membership.sum(values_i)

            return numpy.maximum(0, nb * 100 - 0.5 * amounts - values)

    system = TaxBenefitSystem(multimembers_entities)
    system.add_variables(amount)
    system.add_variables(contribution)
    system.add_variables(value)

    simulation = SimulationBuilder().build_from_dict(system, payload)

    assert (simulation.firm.nb_employees == [2, 0, 1]).all()
    assert (simulation.firm.nb_contracts == [1, 0, 0]).all()
    assert (simulation.firm.nb_expenses == [2, 1, 0]).all()

    contributions = simulation.calculate("contribution", "2026-09")
    assert (
        contributions
        == [
            2 * 100 - 0.5 * 125 - 100,
            (0 * 100 - 0.5 * 50 - 0) * 0,
            1 * 100 - 0.5 * 0 - 0,
        ]
    ).all()
