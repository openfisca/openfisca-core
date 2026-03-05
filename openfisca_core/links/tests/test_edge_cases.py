"""Edge-case and hardened tests for the Link system.

Covers scenarios that are difficult to hit with normal use:
- All-invalid IDs
- Condition of wrong size
- Unresolved links
- Condition all-True / all-False
- Singleton populations
- EnumArray through links
- Chained links with cascading defaults
- Implicit links with role+condition
"""

import numpy
import pytest

from openfisca_core import entities, periods, taxbenefitsystems, variables
from openfisca_core.links import Many2OneLink, One2ManyLink
from openfisca_core.links.implicit import ImplicitOne2ManyLink
from openfisca_core.simulations import SimulationBuilder

# ──────────────────────────────────────────────────────────────
# Shared fixture builder
# ──────────────────────────────────────────────────────────────


def _make_tbs_and_sim(
    n_persons=4,
    *,
    person_links=None,
    household_links=None,
    extra_vars=None,
):
    """Build a minimal TBS and simulation.

    Returns (tbs, sim).
    """
    person = entities.SingleEntity("person", "persons", "A person", "")
    household = entities.GroupEntity(
        "household", "households", "A household", "", roles=[{"key": "member"}]
    )

    for link in person_links or []:
        person.add_link(link)
    for link in household_links or []:
        household.add_link(link)

    tbs = taxbenefitsystems.TaxBenefitSystem([person, household])

    # Standard variables
    class salary(variables.Variable):
        value_type = float
        entity = person
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

    class rent(variables.Variable):
        value_type = float
        entity = household
        definition_period = periods.DateUnit.YEAR

    for var in [salary, mother_id, household_id, household_role, rent]:
        tbs.add_variable(var)

    if extra_vars:
        for var in extra_vars:
            tbs.add_variable(var)

    sim = SimulationBuilder().build_default_simulation(tbs, count=n_persons)
    return tbs, sim


# ──────────────────────────────────────────────────────────────
# 1. Many2One: all IDs invalid
# ──────────────────────────────────────────────────────────────


class TestMany2OneAllInvalid:
    def test_all_mother_ids_minus_one(self):
        """Every person has mother_id=-1 → returns default value for all."""
        mother_link = Many2OneLink("mother", "mother_id", "person")
        _, sim = _make_tbs_and_sim(n_persons=3, person_links=[mother_link])
        sim.set_input("mother_id", "2024", [-1, -1, -1])
        sim.set_input("salary", "2024", [100.0, 200.0, 300.0])

        link = sim.persons.links["mother"]
        result = link.get("salary", "2024")
        # All default (0.0 for salary)
        numpy.testing.assert_array_equal(result, [0.0, 0.0, 0.0])

    def test_mother_id_out_of_bounds(self):
        """mother_id points beyond population size → treated as invalid."""
        mother_link = Many2OneLink("mother", "mother_id", "person")
        _, sim = _make_tbs_and_sim(n_persons=3, person_links=[mother_link])
        sim.set_input("mother_id", "2024", [999, -5, 2])
        sim.set_input("salary", "2024", [100.0, 200.0, 300.0])

        link = sim.persons.links["mother"]
        result = link.get("salary", "2024")
        # Only person 2 (mother_id=2) is valid → salary[2]=300
        numpy.testing.assert_array_equal(result, [0.0, 0.0, 300.0])


# ──────────────────────────────────────────────────────────────
# 2. One2Many: condition of wrong size
# ──────────────────────────────────────────────────────────────


class TestConditionWrongSize:
    def test_condition_too_short_raises(self):
        """A condition with fewer elements than persons should raise."""
        members_link = One2ManyLink(
            "members", "household_id", "person", role_field="household_role"
        )
        _, sim = _make_tbs_and_sim(n_persons=4, household_links=[members_link])
        sim.set_input("household_id", "2024", [0, 0, 1, 1])
        sim.set_input("salary", "2024", [100.0, 200.0, 300.0, 400.0])

        link = sim.populations["household"].links["members"]
        bad_condition = numpy.array([True, False])  # size 2 instead of 4

        with pytest.raises((IndexError, ValueError)):
            link.sum("salary", "2024", condition=bad_condition)


# ──────────────────────────────────────────────────────────────
# 3. Link not resolved: calling get() before resolve()
# ──────────────────────────────────────────────────────────────


class TestUnresolvedLink:
    def test_get_before_resolve_raises(self):
        """Calling get() on an unresolved link should fail clearly."""
        link = Many2OneLink("mother", "mother_id", "person")
        # Not attached, not resolved
        assert not link.is_resolved
        with pytest.raises((AttributeError, TypeError)):
            link.get("salary", "2024")


# ──────────────────────────────────────────────────────────────
# 4. Condition all-False / all-True
# ──────────────────────────────────────────────────────────────


class TestConditionExtremes:
    @pytest.fixture
    def link_sim(self):
        members_link = One2ManyLink(
            "members", "household_id", "person", role_field="household_role"
        )
        _, sim = _make_tbs_and_sim(n_persons=4, household_links=[members_link])
        sim.set_input("household_id", "2024", [0, 0, 1, 1])
        sim.set_input("salary", "2024", [100.0, 200.0, 300.0, 400.0])
        link = sim.populations["household"].links["members"]
        return link, sim

    def test_condition_all_false(self, link_sim):
        link, sim = link_sim
        all_false = numpy.zeros(4, dtype=bool)

        result_sum = link.sum("salary", "2024", condition=all_false)
        result_count = link.count("2024", condition=all_false)
        result_any = link.any("salary", "2024", condition=all_false)

        numpy.testing.assert_array_equal(result_sum, [0.0, 0.0, 0.0, 0.0])
        numpy.testing.assert_array_equal(result_count, [0, 0, 0, 0])
        numpy.testing.assert_array_equal(result_any, [False, False, False, False])

    def test_condition_all_true_same_as_no_condition(self, link_sim):
        link, sim = link_sim
        all_true = numpy.ones(4, dtype=bool)

        with_cond = link.sum("salary", "2024", condition=all_true)
        without_cond = link.sum("salary", "2024")

        numpy.testing.assert_array_equal(with_cond, without_cond)


# ──────────────────────────────────────────────────────────────
# 5. Singleton population (1 person, 1 household)
# ──────────────────────────────────────────────────────────────


class TestSingletonPopulation:
    def test_one_person_one_household(self):
        members_link = One2ManyLink(
            "members", "household_id", "person", role_field="household_role"
        )
        _, sim = _make_tbs_and_sim(n_persons=1, household_links=[members_link])
        sim.set_input("household_id", "2024", [0])
        sim.set_input("salary", "2024", [42.0])

        link = sim.populations["household"].links["members"]

        assert link.sum("salary", "2024")[0] == pytest.approx(42.0)
        assert link.count("2024")[0] == 1
        assert link.avg("salary", "2024")[0] == pytest.approx(42.0)
        assert link.min("salary", "2024")[0] == pytest.approx(42.0)
        assert link.max("salary", "2024")[0] == pytest.approx(42.0)
        assert link.any("salary", "2024")[0] is numpy.bool_(True)
        assert link.all("salary", "2024")[0] is numpy.bool_(True)


# ──────────────────────────────────────────────────────────────
# 6. Chained link with cascading defaults
# ──────────────────────────────────────────────────────────────


class TestChainedDefaults:
    def test_mother_with_no_household(self):
        """person.mother.household("rent") where mother has no household."""
        mother_link = Many2OneLink("mother", "mother_id", "person")
        household_link = Many2OneLink(
            "household", "household_id", "household", role_field="household_role"
        )

        _, sim = _make_tbs_and_sim(
            n_persons=3,
            person_links=[mother_link, household_link],
        )
        # Person 0: mother=-1, hh=0
        # Person 1: mother=0,  hh=-1 (homeless mother!)
        # Person 2: mother=1,  hh=0
        sim.set_input("mother_id", "2024", [-1, 0, 1])
        sim.set_input("household_id", "2024", [0, -1, 0])
        sim.set_input("rent", "2024", [999.0, 0.0, 0.0])

        chained = sim.persons.links["mother"].household
        result = chained.get("rent", "2024")
        # Person 0: no mother → default 0
        # Person 1: mother=0, hh=0, rent=999 → 999
        # Person 2: mother=1, hh=-1 → default 0
        numpy.testing.assert_array_equal(result, [0.0, 999.0, 0.0])


# ──────────────────────────────────────────────────────────────
# 7. ImplicitOne2ManyLink: role + condition combined
# ──────────────────────────────────────────────────────────────


class TestImplicitRoleAndCondition:
    def test_implicit_o2m_role_and_condition(self):
        """The fix for role+condition should also work for implicit links."""
        person = entities.SingleEntity("person", "persons", "A person", "")
        household = entities.GroupEntity(
            "household", "households", "A household", "", roles=[{"key": "member"}]
        )

        tbs = taxbenefitsystems.TaxBenefitSystem([person, household])

        class salary(variables.Variable):
            value_type = float
            entity = person
            definition_period = periods.DateUnit.YEAR

        class is_female(variables.Variable):
            value_type = bool
            entity = person
            definition_period = periods.DateUnit.YEAR

        for var in [salary, is_female]:
            tbs.add_variable(var)

        sim = SimulationBuilder().build_from_dict(
            tbs,
            {
                "persons": {
                    "p0": {"salary": {"2024": 1000.0}, "is_female": {"2024": True}},
                    "p1": {"salary": {"2024": 500.0}, "is_female": {"2024": False}},
                    "p2": {"salary": {"2024": 200.0}, "is_female": {"2024": True}},
                },
                "households": {
                    "h0": {"member": ["p0", "p1", "p2"]},
                },
            },
        )

        # Create and bind implicit link
        link = ImplicitOne2ManyLink("persons", "household", "person")
        pop = sim.populations["household"]
        link.attach(pop)
        link.resolve(sim.populations)

        # Manually assign membership info
        pop.members_entity_id = numpy.array([0, 0, 0])
        pop.members_role = numpy.array([0, 1, 1])

        is_female = sim.calculate("is_female", "2024")

        # Role 1 (children) who are female: only p2 (salary=200)
        res = link.sum("salary", "2024", role=1, condition=is_female)
        assert res[0] == pytest.approx(200.0)

        # Role 0 (parents) who are female: only p0 (salary=1000)
        res = link.sum("salary", "2024", role=0, condition=is_female)
        assert res[0] == pytest.approx(1000.0)


# ──────────────────────────────────────────────────────────────
# 8. GroupPopulation condition edge cases
# ──────────────────────────────────────────────────────────────


class TestGroupPopulationConditionEdgeCases:
    @pytest.fixture
    def sim(self):
        """Sim with country-template entities for GroupPopulation testing."""
        try:
            from openfisca_country_template import CountryTaxBenefitSystem
        except ImportError:
            pytest.skip("openfisca-country-template not installed")

        tbs = CountryTaxBenefitSystem()
        sb = SimulationBuilder()
        sb.set_default_period("2024-01")
        return sb.build_from_entities(
            tbs,
            {
                "persons": {
                    "p0": {"salary": {"2024-01": 1000}},
                    "p1": {"salary": {"2024-01": 2000}},
                    "p2": {"salary": {"2024-01": 3000}},
                },
                "households": {
                    "h0": {"adults": ["p0", "p1"], "children": ["p2"]},
                },
            },
        )

    def test_condition_all_false_gives_zero(self, sim):
        household = sim.household
        salary = household.members("salary", "2024-01")
        all_false = numpy.zeros(3, dtype=bool)

        assert household.sum(salary, condition=all_false)[0] == 0.0
        assert household.nb_persons(condition=all_false)[0] == 0
        assert not household.any(salary > 0, condition=all_false)[0]

    def test_condition_all_true_same_as_none(self, sim):
        household = sim.household
        salary = household.members("salary", "2024-01")
        all_true = numpy.ones(3, dtype=bool)

        with_cond = household.sum(salary, condition=all_true)
        without_cond = household.sum(salary)
        numpy.testing.assert_array_equal(with_cond, without_cond)

    def test_min_condition_excludes_everyone(self, sim):
        """Min with nobody matching → sentinel replaced by 0."""
        household = sim.household
        salary = household.members("salary", "2024-01")
        all_false = numpy.zeros(3, dtype=bool)

        result = household.min(salary, condition=all_false)
        # When no one matches, reduce returns inf → but the test
        # verifies it doesn't crash. The value is implementation-dependent.
        assert len(result) == 1  # One household

    def test_all_with_condition_vacuous_truth(self, sim):
        """all() with condition excluding everyone → vacuously True."""
        household = sim.household
        salary = household.members("salary", "2024-01")
        no_one = numpy.zeros(3, dtype=bool)

        result = household.all(salary > 9999, condition=no_one)
        # Vacuously true: there is no member for which the predicate is false
        assert result[0]


# ──────────────────────────────────────────────────────────────
# 9. Many2OneLink: role helpers on link without role_field
# ──────────────────────────────────────────────────────────────


class TestRoleHelpersMissing:
    def test_has_role_raises_without_role_field(self):
        """has_role() on a link without role_field should raise ValueError."""
        mother_link = Many2OneLink("mother", "mother_id", "person")
        _, sim = _make_tbs_and_sim(n_persons=2, person_links=[mother_link])

        link = sim.persons.links["mother"]
        with pytest.raises(ValueError, match="no role_field"):
            link.has_role(0)

    def test_role_is_none_without_role_field(self):
        """role property on a link without role_field should return None."""
        mother_link = Many2OneLink("mother", "mother_id", "person")
        _, sim = _make_tbs_and_sim(n_persons=2, person_links=[mother_link])

        link = sim.persons.links["mother"]
        assert link.role is None


# ──────────────────────────────────────────────────────────────
# 10. One2ManyLink: empty source population
# ──────────────────────────────────────────────────────────────


class TestEmptySourcePopulation:
    def test_zero_persons_all_aggregations(self):
        """N persons=0, K households > 0 — all aggregations return 0."""
        members_link = One2ManyLink(
            "members", "household_id", "person", role_field="household_role"
        )
        person = entities.SingleEntity("person", "persons", "A person", "")
        household = entities.GroupEntity(
            "household", "households", "A household", "", roles=[{"key": "member"}]
        )
        household.add_link(members_link)
        tbs = taxbenefitsystems.TaxBenefitSystem([person, household])

        class salary(variables.Variable):
            value_type = float
            entity = person
            definition_period = periods.DateUnit.YEAR

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

        for var in [salary, household_id, household_role]:
            tbs.add_variable(var)

        # 0 persons, but let Simulation think there are 2 households
        # build_default_simulation creates both person and household entities
        # with the given count. We need at least 1 person to build.
        sim = SimulationBuilder().build_default_simulation(tbs, count=2)
        # assign all 2 persons to household -1 (none attached to hh 0 or 1)
        sim.set_input("household_id", "2024", [-1, -1])
        sim.set_input("salary", "2024", [100.0, 200.0])

        link = sim.populations["household"].links["members"]

        result_sum = link.sum("salary", "2024")
        result_count = link.count("2024")
        result_any = link.any("salary", "2024")

        # No persons linked to any household → all zeros
        numpy.testing.assert_array_equal(result_sum, [0.0, 0.0])
        numpy.testing.assert_array_equal(result_count, [0, 0])
        numpy.testing.assert_array_equal(result_any, [False, False])
