import numpy
import pytest

from openfisca_core import entities, periods, taxbenefitsystems, variables
from openfisca_core.links import Many2OneLink
from openfisca_core.simulations import SimulationBuilder


@pytest.fixture
def sim():
    person = entities.SingleEntity("person", "persons", "A person", "")
    household = entities.GroupEntity(
        "household", "households", "A household", "", roles=[{"key": "member"}]
    )

    mother_link = Many2OneLink("mother", "mother_id", "person")
    person.add_link(mother_link)

    household_link = Many2OneLink(
        "household", "household_id", "household", role_field="household_role"
    )
    person.add_link(household_link)

    tbs = taxbenefitsystems.TaxBenefitSystem([person, household])

    class age(variables.Variable):
        value_type = int
        entity = person
        definition_period = periods.DateUnit.YEAR

    class rent(variables.Variable):
        value_type = float
        entity = household
        definition_period = periods.DateUnit.YEAR

    class mother_id(variables.Variable):
        value_type = int
        entity = person
        definition_period = periods.DateUnit.ETERNITY
        default_value = -1

    class household_id(variables.Variable):
        value_type = int
        entity = person
        definition_period = periods.DateUnit.ETERNITY
        default_value = -1

    class household_role(variables.Variable):
        value_type = int
        entity = person
        definition_period = periods.DateUnit.ETERNITY
        default_value = 0

    for var in [age, rent, mother_id, household_id, household_role]:
        tbs.add_variable(var)

    # persons: 0, 1, 2, 3
    # households: 0, 1
    sim = SimulationBuilder().build_default_simulation(tbs, count=4)
    # Mother of 0 is -1, 1 is 0, 2 is 0, 3 is 1
    sim.set_input("mother_id", "2024", [-1, 0, 0, 1])
    sim.set_input("age", "2024", [50, 25, 20, 5])
    sim.set_input("household_id", "2024", [0, 0, 1, 1])
    sim.set_input("household_role", "2024", [10, 20, 10, 20])
    sim.set_input("rent", "2024", [800.0, 500.0, 0.0, 0.0])
    return sim


def test_many2one_get_intra_entity(sim):
    """Test person -> person lookup (mother)."""
    link = sim.persons.links["mother"]
    mother_ages = link.get("age", "2024")

    # Expected:
    # 0 -> no mother -> default age (0)
    # 1 -> mother 0 -> age 50
    # 2 -> mother 0 -> age 50
    # 3 -> mother 1 -> age 25
    assert numpy.array_equal(mother_ages, [0, 50, 50, 25])

    # Syntax sugar test:
    assert numpy.array_equal(link("age", "2024"), [0, 50, 50, 25])


def test_many2one_get_inter_entity(sim):
    """Test person -> household lookup."""
    link = sim.persons.links["household"]
    h_rents = link.get("rent", "2024")

    # Expected:
    # 0 -> hh 0 -> rent 800
    # 1 -> hh 0 -> rent 800
    # 2 -> hh 1 -> rent 500
    # 3 -> hh 1 -> rent 500
    assert numpy.array_equal(h_rents, [800.0, 800.0, 500.0, 500.0])


def test_many2one_chaining(sim):
    """Test person.mother.household.rent chaining."""
    mother_link = sim.persons.links["mother"]

    # Expected:
    # person 0 -> mother -1 -> no household -> rent 0.0
    # person 1 -> mother 0 -> hh 0 -> rent 800.0
    # person 2 -> mother 0 -> hh 0 -> rent 800.0
    # person 3 -> mother 1 -> hh 0 -> rent 800.0
    chained_link = mother_link.household
    h_rents = chained_link.get("rent", "2024")
    assert numpy.array_equal(h_rents, [0.0, 800.0, 800.0, 800.0])

    # Test syntactic sugar
    assert numpy.array_equal(chained_link("rent", "2024"), [0.0, 800.0, 800.0, 800.0])


def test_many2one_role_helpers(sim):
    link = sim.persons.links["household"]
    roles = link.role
    assert numpy.array_equal(roles, [10, 20, 10, 20])

    has_role_10 = link.has_role(10)
    assert numpy.array_equal(has_role_10, [True, False, True, False])

    # also exercise the new helper
    parent_rents = link.get_by_role("rent", "2024", role_value=10)
    assert numpy.array_equal(parent_rents, [800.0, 0.0, 500.0, 0.0])


def test_many2one_rank(sim):
    """Ranking people by age within their household via the link.

    The default ``sim`` fixture uses ``build_default_simulation`` which
    does not populate ``household.members_entity_id`` correctly, so we
    patch the group population manually using the input variable.
    """
    # ensure household group mappings match the input variable
    sim.household.members_entity_id = sim.persons("household_id", "2024")
    # reset any cached position so rank uses updated mapping
    sim.household._members_position = None

    link = sim.persons.links["household"]
    # ages [50, 25, 20, 5] per person
    ranks = link.rank("age", "2024")
    # households: h0->[50,25] -> ranks [1,0]; h1->[20,5] -> ranks [1,0]
    assert numpy.array_equal(ranks, [1, 0, 1, 0])

    # chaining should also forward to outer link (no behavioural change)
    chained = sim.persons.links["mother"].household
    ranks2 = chained.rank("age", "2024")
    assert numpy.array_equal(ranks2, ranks)
