import shutil
import tempfile

import numpy
from numpy import testing

from openfisca_country_template import entities, situation_examples

from openfisca_core.simulations import SimulationBuilder
from openfisca_core.taxbenefitsystems import TaxBenefitSystem
from openfisca_core.tools import simulation_dumper


def test_dump(tax_benefit_system) -> None:
    directory = tempfile.mkdtemp(prefix="openfisca_")
    simulation = SimulationBuilder().build_from_entities(
        tax_benefit_system,
        situation_examples.couple,
    )
    calculated_value = simulation.calculate("disposable_income", "2018-01")
    simulation_dumper.dump_simulation(simulation, directory)

    simulation_2 = simulation_dumper.restore_simulation(directory, tax_benefit_system)

    # Check entities structure have been restored

    testing.assert_array_equal(simulation.person.ids, simulation_2.person.ids)
    testing.assert_array_equal(simulation.person.count, simulation_2.person.count)
    testing.assert_array_equal(simulation.household.ids, simulation_2.household.ids)
    testing.assert_array_equal(simulation.household.count, simulation_2.household.count)
    testing.assert_array_equal(
        simulation.household.members_position,
        simulation_2.household.members_position,
    )
    testing.assert_array_equal(
        simulation.household.members_entity_id,
        simulation_2.household.members_entity_id,
    )
    testing.assert_array_equal(
        simulation.household.members_role,
        simulation_2.household.members_role,
    )

    # Check calculated values are in cache

    disposable_income_holder = simulation_2.household.get_holder("disposable_income")
    cached_value = disposable_income_holder.get_array("2018-01")
    assert cached_value is not None
    testing.assert_array_equal(cached_value, calculated_value)

    shutil.rmtree(directory)


def test_dump_restore_with_memberless_group_entity(tax_benefit_system) -> None:
    directory = tempfile.mkdtemp(prefix="openfisca_")
    simulation = SimulationBuilder().build_from_entities(
        tax_benefit_system,
        {
            "persons": {"Alice": {"salary": {"2017-01": 2000}}},
            "households": {"h1": {"adults": ["Alice"]}, "h2": {}},
        },
    )
    simulation.set_input("accommodation_size", "2017-01", numpy.array([60.0, 80.0]))
    simulation_dumper.dump_simulation(simulation, directory)

    simulation_2 = simulation_dumper.restore_simulation(directory, tax_benefit_system)

    assert simulation_2.household.count == 2
    testing.assert_array_equal(simulation.household.ids, simulation_2.household.ids)
    testing.assert_array_equal(
        simulation_2.household.get_holder("accommodation_size").get_array("2017-01"),
        [60.0, 80.0],
    )

    shutil.rmtree(directory)


def test_dump_restore_without_group_entity() -> None:
    directory = tempfile.mkdtemp(prefix="openfisca_")
    person_only_tax_benefit_system = TaxBenefitSystem([entities.Person])
    simulation = SimulationBuilder().build_default_simulation(
        person_only_tax_benefit_system,
        count=2,
    )
    simulation_dumper.dump_simulation(simulation, directory)

    simulation_2 = simulation_dumper.restore_simulation(
        directory,
        person_only_tax_benefit_system,
    )

    assert simulation_2.persons.count == 2

    shutil.rmtree(directory)
