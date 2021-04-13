import shutil
import tempfile

from numpy import testing

from openfisca_country_template import situation_examples

from openfisca_core.tools import simulation_dumper


def test_dump(simulation_builder, tax_benefit_system):
    directory = tempfile.mkdtemp(prefix = "openfisca_")
    simulation = simulation_builder.build_from_entities(tax_benefit_system, situation_examples.couple)
    calculated_value = simulation.calculate('disposable_income', '2018-01')
    simulation_dumper.dump_simulation(simulation, directory)

    simulation_2 = simulation_dumper.restore_simulation(directory, tax_benefit_system)

    # Check entities structure have been restored

    testing.assert_array_equal(simulation.person.ids, simulation_2.person.ids)
    testing.assert_array_equal(simulation.person.count, simulation_2.person.count)
    testing.assert_array_equal(simulation.household.ids, simulation_2.household.ids)
    testing.assert_array_equal(simulation.household.count, simulation_2.household.count)
    testing.assert_array_equal(simulation.household.members_position, simulation_2.household.members_position)
    testing.assert_array_equal(simulation.household.members_entity_id, simulation_2.household.members_entity_id)
    testing.assert_array_equal(simulation.household.members_role, simulation_2.household.members_role)

    # Check calculated values are in cache

    disposable_income_holder = simulation_2.person.get_holder('disposable_income')
    cached_value = disposable_income_holder.get_array('2018-01')
    assert cached_value is not None
    testing.assert_array_equal(cached_value, calculated_value)

    shutil.rmtree(directory)
