# -*- coding: utf-8 -*-


import shutil
import tempfile

from numpy.testing import assert_array_equal

from openfisca_core.tools.simulation_dumper import dump_simulation, restore_simulation


def test_dump(tax_benefit_system, simulation_single):
    directory = tempfile.mkdtemp(prefix = "openfisca_")
    calculated_value = simulation_single.calculate('disposable_income', '2018-01')
    dump_simulation(simulation_single, directory)

    simulation_2 = restore_simulation(directory, tax_benefit_system)

    # Check entities structure have been restored

    assert_array_equal(simulation_single.person.ids, simulation_2.person.ids)
    assert_array_equal(simulation_single.person.count, simulation_2.person.count)
    assert_array_equal(simulation_single.household.ids, simulation_2.household.ids)
    assert_array_equal(simulation_single.household.count, simulation_2.household.count)
    assert_array_equal(simulation_single.household.members_position, simulation_2.household.members_position)
    assert_array_equal(simulation_single.household.members_entity_id, simulation_2.household.members_entity_id)
    assert_array_equal(simulation_single.household.members_role, simulation_2.household.members_role)

    # Check calculated values are in cache

    disposable_income_holder = simulation_2.person.get_holder('disposable_income')
    cached_value = disposable_income_holder.get_array('2018-01')
    assert cached_value is not None
    assert_array_equal(cached_value, calculated_value)

    shutil.rmtree(directory)
