import gc

import numpy
import pytest

from openfisca_country_template.situation_examples import single

from openfisca_core import errors, periods
from openfisca_core.memory_config import MemoryConfig
from openfisca_core.simulations import SimulationBuilder


def test_calculate_full_tracer(tax_benefit_system) -> None:
    simulation = SimulationBuilder().build_default_simulation(tax_benefit_system)
    simulation.trace = True
    simulation.calculate("income_tax", "2017-01")

    income_tax_node = simulation.tracer.trees[0]
    assert income_tax_node.name == "income_tax"
    assert str(income_tax_node.period) == "2017-01"
    assert income_tax_node.value == 0

    salary_node = income_tax_node.children[0]
    assert salary_node.name == "salary"
    assert str(salary_node.period) == "2017-01"
    assert salary_node.parameters == []

    assert len(income_tax_node.parameters) == 1
    assert income_tax_node.parameters[0].name == "taxes.income_tax_rate"
    assert income_tax_node.parameters[0].period == "2017-01-01"
    assert income_tax_node.parameters[0].value == 0.15


def test_get_entity_not_found(tax_benefit_system) -> None:
    simulation = SimulationBuilder().build_default_simulation(tax_benefit_system)
    assert simulation.get_entity(plural="no_such_entities") is None


def test_clone(tax_benefit_system) -> None:
    simulation = SimulationBuilder().build_from_entities(
        tax_benefit_system,
        {
            "persons": {
                "bill": {"salary": {"2017-01": 3000}},
            },
            "households": {"household": {"adults": ["bill"]}},
        },
    )

    simulation_clone = simulation.clone()
    assert simulation != simulation_clone

    for entity_id, entity in simulation.populations.items():
        assert entity != simulation_clone.populations[entity_id]

    assert simulation.persons != simulation_clone.persons

    salary_holder = simulation.person.get_holder("salary")
    salary_holder_clone = simulation_clone.person.get_holder("salary")

    assert salary_holder != salary_holder_clone
    assert salary_holder_clone.simulation == simulation_clone
    assert salary_holder_clone.population == simulation_clone.persons


def new_simulation(tax_benefit_system):
    return SimulationBuilder().build_from_entities(
        tax_benefit_system,
        {
            "persons": {
                "bill": {"salary": {"2017-01": 3000}},
            },
            "households": {"household": {"adults": ["bill"]}},
        },
    )


def test_clone_does_not_share_holder_storage(tax_benefit_system) -> None:
    simulation = new_simulation(tax_benefit_system)
    income_tax_before = simulation.calculate("income_tax", "2017-01")

    clone = simulation.clone()

    # Writing in the clone must not pollute the original
    clone.delete_arrays("salary", "2017-01")
    clone.set_input("salary", "2017-01", numpy.array([6000.0]))
    assert simulation.calculate("salary", "2017-01") == 3000
    assert simulation.calculate("income_tax", "2017-01") == income_tax_before

    # Deleting in the clone must not destroy the original's values
    clone.delete_arrays("salary")
    assert simulation.get_array("salary", "2017-01") is not None


def test_clone_group_entity_holders_bound_to_clone(tax_benefit_system) -> None:
    simulation = new_simulation(tax_benefit_system)
    simulation.calculate("housing_tax", "2017")

    clone = simulation.clone()
    holder_clone = clone.household.get_holder("housing_tax")

    assert holder_clone.population is clone.household
    assert holder_clone.simulation is clone


def test_clone_members_are_cloned(tax_benefit_system) -> None:
    simulation = new_simulation(tax_benefit_system)

    clone = simulation.clone()

    assert clone.household.members is clone.persons


def test_clone_does_not_share_invalidated_caches(tax_benefit_system) -> None:
    simulation = new_simulation(tax_benefit_system)

    clone = simulation.clone()

    assert clone.invalidated_caches is not simulation.invalidated_caches


@pytest.mark.filterwarnings("ignore")
def test_clone_disk_storage_is_isolated(tax_benefit_system) -> None:
    simulation = new_simulation(tax_benefit_system)
    simulation.memory_config = MemoryConfig(max_memory_occupation=0.0)
    # Materialize the on-disk storage before cloning, so that the clone
    # actually has to disentangle itself from the original's directory.
    simulation.set_input("age", "2017-01", numpy.array([30]))

    clone = simulation.clone()

    clone.delete_arrays("age", "2017-01")
    clone.set_input("age", "2017-01", numpy.array([99]))
    assert simulation.calculate("age", "2017-01") == 30

    # "birth" has no holder yet: each simulation lazily creates its own,
    # which must not end up writing into the same directory.
    simulation.set_input("birth", "2017-01", numpy.array(["1987-01-01"]))
    clone.set_input("birth", "2017-01", numpy.array(["1999-01-01"]))
    assert simulation.calculate("birth", "2017-01") == numpy.datetime64("1987-01-01")

    # Garbage-collecting the clone must not destroy the original's files
    del clone
    gc.collect()
    assert simulation.calculate("age", "2017-01") == 30
    assert simulation.calculate("birth", "2017-01") == numpy.datetime64("1987-01-01")


@pytest.mark.filterwarnings("ignore")
def test_clone_disk_storage_preserves_enums(tax_benefit_system) -> None:
    simulation = new_simulation(tax_benefit_system)
    simulation.memory_config = MemoryConfig(max_memory_occupation=0.0)
    simulation.set_input("housing_occupancy_status", "2017-01", numpy.array(["tenant"]))

    clone = simulation.clone()

    status = clone.calculate("housing_occupancy_status", "2017-01")
    assert status.decode_to_str() == ["tenant"]


def test_get_memory_usage(tax_benefit_system) -> None:
    simulation = SimulationBuilder().build_from_entities(tax_benefit_system, single)
    simulation.calculate("disposable_income", "2017-01")
    memory_usage = simulation.get_memory_usage(variables=["salary"])
    assert memory_usage["total_nb_bytes"] > 0
    assert len(memory_usage["by_variable"]) == 1


def test_invalidate_cache_when_spiral_error_detected(tax_benefit_system) -> None:
    simulation = SimulationBuilder().build_default_simulation(tax_benefit_system)
    tracer = simulation.tracer

    tracer.record_calculation_start("a", periods.period(2017))
    tracer.record_calculation_start("b", periods.period(2016))
    tracer.record_calculation_start("a", periods.period(2016))

    with pytest.raises(errors.SpiralError):
        simulation._check_for_cycle("a", periods.period(2016))

    assert len(simulation.invalidated_caches) == 3
