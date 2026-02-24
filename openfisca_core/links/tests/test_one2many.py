import numpy
import pytest

from openfisca_core import entities, periods, taxbenefitsystems, variables
from openfisca_core.links import One2ManyLink
from openfisca_core.simulations import SimulationBuilder


@pytest.fixture
def sim():
    person = entities.SingleEntity("person", "persons", "A person", "")
    household = entities.GroupEntity("household", "households", "A household", "", roles=[{"key": "member"}])

    members_link = One2ManyLink("members", "household_id", "person", role_field="household_role")
    household.add_link(members_link)

    tbs = taxbenefitsystems.TaxBenefitSystem([person, household])

    class salary(variables.Variable):
        value_type = float
        entity = person
        definition_period = periods.DateUnit.YEAR

    class is_female(variables.Variable):
        value_type = bool
        entity = person
        definition_period = periods.DateUnit.YEAR

    class household_id(variables.Variable):
        value_type = int
        entity = person
        definition_period = periods.DateUnit.ETERNITY
        default_value = -1

    class household_role(variables.Variable): # 0: parent, 1: child
        value_type = int
        entity = person
        definition_period = periods.DateUnit.ETERNITY
        default_value = 0

    for var in [salary, is_female, household_id, household_role]:
        tbs.add_variable(var)

    sim = SimulationBuilder().build_default_simulation(tbs, count=4)
    # households: 0, 1
    # person 0: hh 0, role 0, salary 1000, F
    # person 1: hh 0, role 1, salary 500,  M
    # person 2: hh 1, role 0, salary 2000, M
    # person 3: hh -1 (none)
    sim.set_input("household_id", "2024", [0, 0, 1, -1])
    sim.set_input("household_role", "2024", [0, 1, 0, 0])
    sim.set_input("salary", "2024", [1000.0, 500.0, 2000.0, 100.0])
    sim.set_input("is_female", "2024", [True, False, False, True])

    return sim


def test_one2many_aggregations(sim):
    link = sim.populations["household"].links["members"]

    res_sum = link.sum("salary", "2024")
    assert numpy.array_equal(res_sum, [1500.0, 2000.0, 0.0, 0.0])

    res_count = link.count("2024")
    assert numpy.array_equal(res_count, [2, 1, 0, 0])

    res_avg = link.avg("salary", "2024")
    assert numpy.array_equal(res_avg, [750.0, 2000.0, 0.0, 0.0])

    res_min = link.min("salary", "2024")
    assert numpy.array_equal(res_min, [500.0, 2000.0, 0.0, 0.0])

    res_max = link.max("salary", "2024")
    assert numpy.array_equal(res_max, [1000.0, 2000.0, 0.0, 0.0])


def test_one2many_any_all(sim):
    link = sim.populations["household"].links["members"]

    # Is there a female in each household?
    res_any = link.any("is_female", "2024")
    assert numpy.array_equal(res_any, [True, False, False, False])

    # Are all members female?
    res_all = link.all("is_female", "2024")
    assert numpy.array_equal(res_all, [False, False, True, True])


def test_one2many_role_filter(sim):
    link = sim.populations["household"].links["members"]

    # Count of role 1 (child)
    # hh 0 has person 1 (role 1)
    res_count = link.count("2024", role=1)
    assert numpy.array_equal(res_count, [1, 0, 0, 0])

    # Sum salary of role 1
    res_sum = link.sum("salary", "2024", role=1)
    assert numpy.array_equal(res_sum, [500.0, 0.0, 0.0, 0.0])


def test_one2many_condition_filter(sim):
    link = sim.populations["household"].links["members"]
    condition = sim.calculate("is_female", "2024")

    # Sum of salary for females only
    res_sum = link.sum("salary", "2024", condition=condition)
    assert numpy.array_equal(res_sum, [1000.0, 0.0, 0.0, 0.0])
