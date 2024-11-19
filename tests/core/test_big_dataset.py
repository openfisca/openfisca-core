from copy import deepcopy
from time import time
from openfisca_country_template import entities, situation_examples
from collections.abc import Iterable
from openfisca_core import tools
from openfisca_core.simulations import SimulationBuilder
from openfisca_core.tools import test_runner

import random
from unittest import TestCase

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

    tc.assertEqual(simulation.calculate_add("salary", period).sum(), sum(persons_salaries))
    tc.assertEqual(
        simulation.calculate_add("rent", period).sum(), sum(households_rents)
    )
    total_taxes = simulation.calculate_add("total_taxes", period).sum()
    tc.assertAlmostEqual(total_taxes, sum(persons_salaries)*0.17833333, delta=1)

def test_speed(tax_benefit_system):
    elapsed = 0
    for _ in range(10):
        start = time()
        run_simulation(tax_benefit_system)
        end = time()
        elapsed += end - start
    elapsed_mean = elapsed / 10
    print(f"Mean elapsed time: {elapsed_mean:.2f} seconds")
    tc.assertLess(elapsed_mean, 0.3)