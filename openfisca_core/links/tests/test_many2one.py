import numpy
import pytest

from openfisca_core import entities, periods, taxbenefitsystems, variables
from openfisca_core.links import Many2OneLink
from openfisca_core.populations import ADD, DIVIDE
from openfisca_core.populations._errors import IncompatibleOptionsError
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
    # ensure household group mappings match the input variable (4 persons → 2 households)
    sim.household.members_entity_id = sim.persons("household_id", "2024")
    sim.household.count = 2  # match number of entities implied by members_entity_id
    # reset cached caches so rank uses updated mapping (members_position
    # and ordered_members_map must both be recomputed from new members_entity_id)
    sim.household._members_position = None
    sim.household._ordered_members_map = None

    link = sim.persons.links["household"]
    # ages [50, 25, 20, 5] per person
    ranks = link.rank("age", "2024")
    # households: h0->[50,25] -> ranks [1,0]; h1->[20,5] -> ranks [1,0]
    assert numpy.array_equal(ranks, [1, 0, 1, 0])


# -- Many2OneLink options (ADD / DIVIDE) -----------------------------------


def test_many2one_call_accepts_options_keyword(sim):
    """Link __call__ accepts options= and forwards to get(); ADD over one year = same as calculate."""
    link = sim.persons.links["household"]
    # rent is YEAR; ADD over "2024" (one subperiod) equals plain calculate
    without_options = link("rent", "2024")
    with_add = link("rent", "2024", options=[ADD])
    assert numpy.array_equal(without_options, with_add)
    assert numpy.array_equal(link.get("rent", "2024", options=None), without_options)


def test_many2one_get_with_options_add(sim):
    """Link.get(..., options=[ADD]) returns same as target population calculate_add projected."""
    link = sim.persons.links["household"]
    # Direct get with options
    result = link.get("rent", "2024", options=[ADD])
    # Should match household.calculate_add projected to persons via link
    expected = sim.household("rent", "2024", options=[ADD])
    person_household_ids = sim.persons("household_id", "2024")
    expected_per_person = numpy.array(
        [expected[i] for i in person_household_ids],
        dtype=expected.dtype,
    )
    assert numpy.array_equal(result, expected_per_person)


def test_many2one_call_options_incompatible(sim):
    """Link __call__ with both ADD and DIVIDE raises IncompatibleOptionsError."""
    link = sim.persons.links["household"]
    with pytest.raises(IncompatibleOptionsError):
        link("rent", "2024", options=[ADD, DIVIDE])


def test_many2one_chained_call_with_options(sim):
    """Chained link (person.mother.household) accepts options= in __call__ and get."""
    chained = sim.persons.links["mother"].household
    without_options = chained("rent", "2024")
    with_add = chained("rent", "2024", options=[ADD])
    assert numpy.array_equal(without_options, with_add)
    with_add_get = chained.get("rent", "2024", options=[ADD])
    assert numpy.array_equal(with_add_get, without_options)


# -- User-facing errors for invalid use ---------------------------------------


def test_get_rank_requires_group_entity_raises(sim):
    """get_rank(link to single entity) raises a clear ValueError."""
    # person.mother is a link to person (single entity); rank requires a group
    chained = sim.persons.links["mother"].household
    with pytest.raises(ValueError, match="get_rank requires a group entity"):
        chained.rank("age", "2024")


def test_value_nth_person_inconsistent_group_raises(sim):
    """value_nth_person raises clear ValueError when count != entities from members_entity_id."""
    # Mistake: patch members_entity_id to 2 entities but leave count=4
    sim.household.members_entity_id = sim.persons(
        "household_id", "2024"
    )  # [0,0,1,1] -> 2 entities
    sim.household._members_position = None
    sim.household._ordered_members_map = None
    # do NOT set sim.household.count = 2
    link = sim.persons.links["household"]
    with pytest.raises(ValueError, match="Group population .* is inconsistent"):
        link.rank("age", "2024")
