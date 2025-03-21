import numpy
import pytest

from openfisca_country_template import situation_examples
from openfisca_country_template.variables import housing

from openfisca_core import holders, periods, tools
from openfisca_core.errors import PeriodMismatchError
from openfisca_core.experimental import MemoryConfig
from openfisca_core.holders import Holder
from openfisca_core.periods import DateUnit
from openfisca_core.simulations import SimulationBuilder


@pytest.fixture
def single(tax_benefit_system):
    return SimulationBuilder().build_from_entities(
        tax_benefit_system,
        situation_examples.single,
    )


@pytest.fixture
def couple(tax_benefit_system):
    return SimulationBuilder().build_from_entities(
        tax_benefit_system,
        situation_examples.couple,
    )


period = periods.period("2017-12")


def test_set_input_enum_string(couple) -> None:
    simulation = couple
    status_occupancy = numpy.asarray(["free_lodger"])
    simulation.household.get_holder("housing_occupancy_status").set_input(
        period,
        status_occupancy,
    )
    result = simulation.calculate("housing_occupancy_status", period)
    assert result == housing.HousingOccupancyStatus.free_lodger


def test_set_input_enum_int(couple) -> None:
    simulation = couple
    status_occupancy = numpy.asarray([2], dtype=numpy.int16)
    simulation.household.get_holder("housing_occupancy_status").set_input(
        period,
        status_occupancy,
    )
    result = simulation.calculate("housing_occupancy_status", period)
    assert result == housing.HousingOccupancyStatus.free_lodger


def test_set_input_enum_item(couple) -> None:
    simulation = couple
    status_occupancy = numpy.asarray([housing.HousingOccupancyStatus.free_lodger])
    simulation.household.get_holder("housing_occupancy_status").set_input(
        period,
        status_occupancy,
    )
    result = simulation.calculate("housing_occupancy_status", period)
    assert result == housing.HousingOccupancyStatus.free_lodger


def test_yearly_input_month_variable(couple) -> None:
    with pytest.raises(PeriodMismatchError) as error:
        couple.set_input("rent", 2019, 3000)
    assert (
        'Unable to set a value for variable "rent" for year-long period'
        in error.value.message
    )


def test_3_months_input_month_variable(couple) -> None:
    with pytest.raises(PeriodMismatchError) as error:
        couple.set_input("rent", "month:2019-01:3", 3000)
    assert (
        'Unable to set a value for variable "rent" for 3-months-long period'
        in error.value.message
    )


def test_month_input_year_variable(couple) -> None:
    with pytest.raises(PeriodMismatchError) as error:
        couple.set_input("housing_tax", "2019-01", 3000)
    assert (
        'Unable to set a value for variable "housing_tax" for month-long period'
        in error.value.message
    )


def test_enum_dtype(couple) -> None:
    simulation = couple
    status_occupancy = numpy.asarray([2], dtype=numpy.int16)
    simulation.household.get_holder("housing_occupancy_status").set_input(
        period,
        status_occupancy,
    )
    result = simulation.calculate("housing_occupancy_status", period)
    assert result.dtype.kind is not None


def test_permanent_variable_empty(single) -> None:
    simulation = single
    holder = simulation.person.get_holder("birth")
    assert holder.get_array(None) is None


def test_permanent_variable_filled(single) -> None:
    simulation = single
    holder = simulation.person.get_holder("birth")
    value = numpy.asarray(["1980-01-01"], dtype=holder.variable.dtype)
    holder.set_input(periods.period(DateUnit.ETERNITY), value)
    assert holder.get_array(None) == value
    assert holder.get_array(DateUnit.ETERNITY) == value
    assert holder.get_array("2016-01") == value


def test_delete_arrays(single) -> None:
    simulation = single
    salary_holder = simulation.person.get_holder("salary")
    salary_holder.set_input(periods.period(2017), numpy.asarray([30000]))
    salary_holder.set_input(periods.period(2018), numpy.asarray([60000]))
    assert simulation.person("salary", "2017-01") == 2500
    assert simulation.person("salary", "2018-01") == 5000
    salary_holder.delete_arrays(period=2018)

    salary_array = simulation.get_array("salary", "2017-01")
    assert salary_array is not None
    salary_array = simulation.get_array("salary", "2018-01")
    assert salary_array is None

    salary_holder.set_input(periods.period(2018), numpy.asarray([15000]))
    assert simulation.person("salary", "2017-01") == 2500
    assert simulation.person("salary", "2018-01") == 1250


def test_get_memory_usage(single) -> None:
    simulation = single
    salary_holder = simulation.person.get_holder("salary")
    memory_usage = salary_holder.get_memory_usage()
    assert memory_usage["total_nb_bytes"] == 0
    salary_holder.set_input(periods.period(2017), numpy.asarray([30000]))
    memory_usage = salary_holder.get_memory_usage()
    assert memory_usage["nb_cells_by_array"] == 1
    assert memory_usage["cell_size"] == 4  # float 32
    assert memory_usage["nb_cells_by_array"] == 1  # one person
    assert memory_usage["nb_arrays"] == 12  # 12 months
    assert memory_usage["total_nb_bytes"] == 4 * 12 * 1


def test_get_memory_usage_with_trace(single) -> None:
    simulation = single
    simulation.trace = True
    salary_holder = simulation.person.get_holder("salary")
    salary_holder.set_input(periods.period(2017), numpy.asarray([30000]))
    simulation.calculate("salary", "2017-01")
    simulation.calculate("salary", "2017-01")
    simulation.calculate("salary", "2017-02")
    simulation.calculate_add("salary", "2017")  # 12 calculations
    memory_usage = salary_holder.get_memory_usage()
    assert memory_usage["nb_requests"] == 15
    assert memory_usage["nb_requests_by_array"] == 1.25  # 15 calculations / 12 arrays


def test_set_input_dispatch_by_period(single) -> None:
    simulation = single
    variable = simulation.tax_benefit_system.get_variable("housing_occupancy_status")
    entity = simulation.household
    holder = Holder(variable, entity)
    holders.set_input_dispatch_by_period(holder, periods.period(2019), "owner")
    assert holder.get_array("2019-01") == holder.get_array(
        "2019-12",
    )  # Check the feature
    assert holder.get_array("2019-01") is holder.get_array(
        "2019-12",
    )  # Check that the vectors are the same in memory, to avoid duplication


force_storage_on_disk = MemoryConfig(max_memory_occupation=0)


def test_delete_arrays_on_disk(single) -> None:
    simulation = single
    simulation.memory_config = force_storage_on_disk
    salary_holder = simulation.person.get_holder("salary")
    salary_holder.set_input(periods.period(2017), numpy.asarray([30000]))
    salary_holder.set_input(periods.period(2018), numpy.asarray([60000]))
    assert simulation.person("salary", "2017-01") == 2500
    assert simulation.person("salary", "2018-01") == 5000
    salary_holder.delete_arrays(period=2018)
    salary_holder.set_input(periods.period(2018), numpy.asarray([15000]))
    assert simulation.person("salary", "2017-01") == 2500
    assert simulation.person("salary", "2018-01") == 1250


def test_cache_disk(couple) -> None:
    simulation = couple
    simulation.memory_config = force_storage_on_disk
    month = periods.period("2017-01")
    holder = simulation.household.get_holder("disposable_income")
    data = numpy.asarray([2000])
    holder.put_in_cache(data, month)
    stored_data = holder.get_array(month)
    tools.assert_near(data, stored_data)


def test_known_periods(couple) -> None:
    simulation = couple
    simulation.memory_config = force_storage_on_disk
    month = periods.period("2017-01")
    month_2 = periods.period("2017-02")
    holder = simulation.household.get_holder("disposable_income")
    data = numpy.asarray([2000])
    holder.put_in_cache(data, month)
    holder._memory_storage.put(data, month_2)

    assert sorted(holder.get_known_periods()), [month == month_2]


def test_cache_enum_on_disk(single) -> None:
    simulation = single
    simulation.memory_config = force_storage_on_disk
    month = periods.period("2017-01")
    simulation.calculate("housing_occupancy_status", month)  # First calculation
    housing_occupancy_status = simulation.calculate(
        "housing_occupancy_status",
        month,
    )  # Read from cache
    assert housing_occupancy_status == housing.HousingOccupancyStatus.tenant


def test_set_not_cached_variable(single) -> None:
    dont_cache_variable = MemoryConfig(
        max_memory_occupation=1,
        variables_to_drop=["salary"],
    )
    simulation = single
    simulation.memory_config = dont_cache_variable
    holder = simulation.person.get_holder("salary")
    array = numpy.asarray([2000])
    holder.set_input("2015-01", array)
    assert simulation.calculate("salary", "2015-01") == array


def test_set_input_float_to_int(single) -> None:
    simulation = single
    age = numpy.asarray([50.6])
    simulation.person.get_holder("age").set_input(period, age)
    result = simulation.calculate("age", period)
    assert result == numpy.asarray([50])
