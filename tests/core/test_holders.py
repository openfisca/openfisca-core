# -*- coding: utf-8 -*-

import numpy as np
import pytest
from pytest import fixture

import openfisca_country_template.situation_examples
from openfisca_country_template.variables.housing import HousingOccupancyStatus

from openfisca_core.errors import PeriodMismatchError
from openfisca_core.holders import Holder, set_input_dispatch_by_period
from openfisca_core.memory_config import MemoryConfig
from openfisca_core.periods import ETERNITY, period as make_period
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_core.tools import assert_near
from .test_countries import tax_benefit_system


@fixture
def single():
    return SimulationBuilder().build_from_entities(tax_benefit_system, openfisca_country_template.situation_examples.single)


@fixture
def couple():
    return SimulationBuilder().build_from_entities(tax_benefit_system, openfisca_country_template.situation_examples.couple)


period = make_period('2017-12')


def test_set_input_enum_string(couple):
    simulation = couple
    status_occupancy = np.asarray(['free_lodger'])
    simulation.household.get_holder('housing_occupancy_status').set_input(period, status_occupancy)
    result = simulation.calculate('housing_occupancy_status', period)
    assert result == HousingOccupancyStatus.free_lodger


def test_set_input_enum_int(couple):
    simulation = couple
    status_occupancy = np.asarray([2], dtype = np.int16)
    simulation.household.get_holder('housing_occupancy_status').set_input(period, status_occupancy)
    result = simulation.calculate('housing_occupancy_status', period)
    assert result == HousingOccupancyStatus.free_lodger


def test_set_input_enum_item(couple):
    simulation = couple
    status_occupancy = np.asarray([HousingOccupancyStatus.free_lodger])
    simulation.household.get_holder('housing_occupancy_status').set_input(period, status_occupancy)
    result = simulation.calculate('housing_occupancy_status', period)
    assert result == HousingOccupancyStatus.free_lodger


def test_yearly_input_month_variable(couple):
    with pytest.raises(PeriodMismatchError) as error:
        couple.set_input('rent', 2019, 3000)
    assert 'Unable to set a value for variable "rent" for year-long period' in error.value.message


def test_3_months_input_month_variable(couple):
    with pytest.raises(PeriodMismatchError) as error:
        couple.set_input('rent', 'month:2019-01:3', 3000)
    assert 'Unable to set a value for variable "rent" for 3-months-long period' in error.value.message


def test_month_input_year_variable(couple):
    with pytest.raises(PeriodMismatchError) as error:
        couple.set_input('housing_tax', '2019-01', 3000)
    assert 'Unable to set a value for variable "housing_tax" for month-long period' in error.value.message


def test_enum_dtype(couple):
    simulation = couple
    status_occupancy = np.asarray([2], dtype = np.int16)
    simulation.household.get_holder('housing_occupancy_status').set_input(period, status_occupancy)
    result = simulation.calculate('housing_occupancy_status', period)
    assert result.dtype.kind is not None


def test_permanent_variable_empty(single):
    simulation = single
    holder = simulation.person.get_holder('birth')
    assert holder.get_array(None) is None


def test_permanent_variable_filled(single):
    simulation = single
    holder = simulation.person.get_holder('birth')
    value = np.asarray(['1980-01-01'], dtype = holder.variable.dtype)
    holder.set_input(make_period(ETERNITY), value)
    assert holder.get_array(None) == value
    assert holder.get_array(ETERNITY) == value
    assert holder.get_array('2016-01') == value


def test_delete_arrays(single):
    simulation = single
    salary_holder = simulation.person.get_holder('salary')
    salary_holder.set_input(make_period(2017), np.asarray([30000]))
    salary_holder.set_input(make_period(2018), np.asarray([60000]))
    assert simulation.person('salary', '2017-01') == 2500
    assert simulation.person('salary', '2018-01') == 5000
    salary_holder.delete_arrays(period = 2018)
    salary_holder.set_input(make_period(2018), np.asarray([15000]))
    assert simulation.person('salary', '2017-01') == 2500
    assert simulation.person('salary', '2018-01') == 1250


def test_get_memory_usage(single):
    simulation = single
    salary_holder = simulation.person.get_holder('salary')
    memory_usage = salary_holder.get_memory_usage()
    assert memory_usage['total_nb_bytes'] == 0
    salary_holder.set_input(make_period(2017), np.asarray([30000]))
    memory_usage = salary_holder.get_memory_usage()
    assert memory_usage['nb_cells_by_array'] == 1
    assert memory_usage['cell_size'] == 4  # float 32
    assert memory_usage['nb_cells_by_array'] == 1  # one person
    assert memory_usage['nb_arrays'] == 12  # 12 months
    assert memory_usage['total_nb_bytes'] == 4 * 12 * 1


def test_get_memory_usage_with_trace(single):
    simulation = single
    simulation.trace = True
    salary_holder = simulation.person.get_holder('salary')
    salary_holder.set_input(make_period(2017), np.asarray([30000]))
    simulation.calculate('salary', '2017-01')
    simulation.calculate('salary', '2017-01')
    simulation.calculate('salary', '2017-02')
    simulation.calculate_add('salary', '2017')  # 12 calculations
    memory_usage = salary_holder.get_memory_usage()
    assert memory_usage['nb_requests'] == 15
    assert memory_usage['nb_requests_by_array'] == 1.25  # 15 calculations / 12 arrays


def test_set_input_dispatch_by_period(single):
    simulation = single
    variable = simulation.tax_benefit_system.get_variable('housing_occupancy_status')
    entity = simulation.household
    holder = Holder(variable, entity)
    set_input_dispatch_by_period(holder, make_period(2019), 'owner')
    assert holder.get_array('2019-01') == holder.get_array('2019-12')  # Check the feature
    assert holder.get_array('2019-01') is holder.get_array('2019-12')  # Check that the vectors are the same in memory, to avoid duplication


force_storage_on_disk = MemoryConfig(max_memory_occupation = 0)


def test_delete_arrays_on_disk(single):
    simulation = single
    simulation.memory_config = force_storage_on_disk
    salary_holder = simulation.person.get_holder('salary')
    salary_holder.set_input(make_period(2017), np.asarray([30000]))
    salary_holder.set_input(make_period(2018), np.asarray([60000]))
    assert simulation.person('salary', '2017-01') == 2500
    assert simulation.person('salary', '2018-01') == 5000
    salary_holder.delete_arrays(period = 2018)
    salary_holder.set_input(make_period(2018), np.asarray([15000]))
    assert simulation.person('salary', '2017-01') == 2500
    assert simulation.person('salary', '2018-01') == 1250


def test_cache_disk(couple):
    simulation = couple
    simulation.memory_config = force_storage_on_disk
    month = make_period('2017-01')
    holder = simulation.person.get_holder('disposable_income')
    data = np.asarray([2000, 3000])
    holder.put_in_cache(data, month)
    stored_data = holder.get_array(month)
    assert_near(data, stored_data)


def test_known_periods(couple):
    simulation = couple
    simulation.memory_config = force_storage_on_disk
    month = make_period('2017-01')
    month_2 = make_period('2017-02')
    holder = simulation.person.get_holder('disposable_income')
    data = np.asarray([2000, 3000])
    holder.put_in_cache(data, month)
    holder._memory_storage.put(data, month_2)

    assert sorted(holder.get_known_periods()), [month == month_2]


def test_cache_enum_on_disk(single):
    simulation = single
    simulation.memory_config = force_storage_on_disk
    month = make_period('2017-01')
    simulation.calculate('housing_occupancy_status', month)  # First calculation
    housing_occupancy_status = simulation.calculate('housing_occupancy_status', month)  # Read from cache
    assert housing_occupancy_status == HousingOccupancyStatus.tenant


def test_set_not_cached_variable(single):
    dont_cache_variable = MemoryConfig(max_memory_occupation = 1, variables_to_drop = ['salary'])
    simulation = single
    simulation.memory_config = dont_cache_variable
    holder = simulation.person.get_holder('salary')
    array = np.asarray([2000])
    holder.set_input('2015-01', array)
    assert simulation.calculate('salary', '2015-01') == array


def test_set_input_float_to_int(single):
    simulation = single
    age = np.asarray([50.6])
    simulation.person.get_holder('age').set_input(period, age)
    result = simulation.calculate('age', period)
    assert result == np.asarray([50])
