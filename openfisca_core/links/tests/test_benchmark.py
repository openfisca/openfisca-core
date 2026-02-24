import pytest
import numpy
from openfisca_core import entities, periods, taxbenefitsystems, variables
from openfisca_core.simulations import SimulationBuilder


def build_large_simulation(n_households=5000, persons_per_hh=3):
    person = entities.SingleEntity("person", "persons", "A person", "")
    household = entities.GroupEntity("household", "households", "A household", "", roles=[{"key": "member"}])

    tbs = taxbenefitsystems.TaxBenefitSystem([person, household])

    class salary(variables.Variable):
        value_type = float
        entity = person
        definition_period = periods.DateUnit.YEAR

    class rent(variables.Variable):
        value_type = float
        entity = household
        definition_period = periods.DateUnit.YEAR

    for var in [salary, rent]:
        tbs.add_variable(var)

    # Generate data
    n_persons = n_households * persons_per_hh

    persons_dict = {
        f"p{i}": {"salary": {"2024": float(i % 1000)}}
        for i in range(n_persons)
    }

    households_dict = {
        f"h{i}": {
            "member": [f"p{i * persons_per_hh + j}" for j in range(persons_per_hh)],
            "rent": {"2024": float(i % 500)}
        }
        for i in range(n_households)
    }

    input_dict = {
        "persons": persons_dict,
        "households": households_dict
    }

    return SimulationBuilder().build_from_dict(tbs, input_dict)


@pytest.fixture(scope="module")
def sim():
    return build_large_simulation()


def test_benchmark_projector_m2o(benchmark, sim):
    """Benchmark the old projector logic: person.household('rent', period)."""
    def compute():
        # Get variable rent via projector
        # the shortcut triggers projector_function
        return sim.persons.household("rent", "2024")

    res = benchmark(compute)
    assert len(res) == sim.persons.count


def test_benchmark_link_m2o(benchmark, sim):
    """Benchmark the new link logic: person.links['household'].get('rent', period)."""
    def compute():
        return sim.persons.links["household"].get("rent", "2024")

    res = benchmark(compute)
    assert len(res) == sim.persons.count


def test_benchmark_old_sum_o2m(benchmark, sim):
    """Benchmark the old GroupPopulation sum: household.sum(persons('salary', period))."""
    def compute():
        salaries = sim.persons("salary", "2024")
        return sim.populations["household"].sum(salaries)

    res = benchmark(compute)
    assert len(res) == sim.populations["household"].count


def test_benchmark_link_sum_o2m(benchmark, sim):
    """Benchmark the new link sum: household.links['persons'].sum('salary', period)."""
    def compute():
        return sim.populations["household"].links["persons"].sum("salary", "2024")

    res = benchmark(compute)
    assert len(res) == sim.populations["household"].count
