from collections.abc import Iterable

from unittest import TestCase

from openfisca_core.simulations import SimulationBuilder

tc = TestCase()


NUM_PERSONS = 50_000

YEAR = 2023
MONTH = "2023-12"


def run_simulation(tax_benefit_system) -> None:
    persons_per_households = 2
    persons_ids: Iterable = [p for p in range(NUM_PERSONS)]
    households_ids: Iterable = [
        f"h{i}" for i in range(NUM_PERSONS // persons_per_households)
    ]

    persons_households: Iterable = [
        f"h{i // persons_per_households}" for i in range(NUM_PERSONS)
    ]

    persons_salaries: Iterable = [1_000 for i in range(NUM_PERSONS)]
    households_rents = [500 for i in range(NUM_PERSONS // persons_per_households)]

    period = MONTH

    simulation_builder = SimulationBuilder()
    simulation_builder.create_entities(tax_benefit_system)
    simulation_builder.declare_person_entity("person", persons_ids)

    household_instance = simulation_builder.declare_entity("household", households_ids)
    simulation_builder.join_with_persons(
        household_instance,
        persons_households,
        ["first_parent"] * NUM_PERSONS,
    )

    simulation = simulation_builder.build(tax_benefit_system)
    simulation.set_input("salary", period, persons_salaries)
    simulation.set_input("rent", period, households_rents)

    tc.assertEqual(
        simulation.calculate_add("salary", period).sum(), sum(persons_salaries)
    )
    tc.assertEqual(
        simulation.calculate_add("rent", period).sum(), sum(households_rents)
    )
    total_taxes = simulation.calculate_add("total_taxes", period).sum()
    tc.assertAlmostEqual(total_taxes, sum(persons_salaries) * 0.17833333, delta=1)


def test_speed(tax_benefit_system, benchmark) -> None:
    def run() -> None:
        run_simulation(tax_benefit_system)
    result = benchmark.pedantic(run, iterations=1, rounds=10)
    assert not result
