"""Thorough logic tests for One2ManyLink aggregation methods.

Tests cover:
- Combined role + condition filters
- All aggregation methods (sum, count, avg, min, max, any, all) with filters
- Edge cases: empty households, single-member households, negative values
- Vacuous truth for `all()` on empty groups
- `avg()` with zero-count groups (division by zero guard)
- Implicit One2Many links with filters
"""

import numpy
import pytest

from openfisca_core import entities, periods, taxbenefitsystems, variables
from openfisca_core.links import One2ManyLink
from openfisca_core.simulations import SimulationBuilder


@pytest.fixture
def rich_sim():
    """Simulation with 6 persons and 3 households, various edge cases.

    - hh 0: person 0 (role 0, parent, F, salary 1000),
      person 1 (role 1, child, M, salary -200),
      person 2 (role 1, child, F, salary 300)
    - hh 1: person 3 (role 0, parent, M, salary 5000)
    - hh 2: empty (no persons assigned)
    - person 4: household_id = -1 (unattached)
    - person 5: household_id = -1 (unattached)
    """
    person = entities.SingleEntity("person", "persons", "A person", "")
    household = entities.GroupEntity(
        "household", "households", "A household", "", roles=[{"key": "member"}]
    )

    members_link = One2ManyLink(
        "members", "household_id", "person", role_field="household_role"
    )
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

    class is_student(variables.Variable):
        value_type = bool
        entity = person
        definition_period = periods.DateUnit.YEAR

    class household_id(variables.Variable):
        value_type = int
        entity = person
        definition_period = periods.DateUnit.ETERNITY
        default_value = -1

    class household_role(variables.Variable):  # 0: parent, 1: child
        value_type = int
        entity = person
        definition_period = periods.DateUnit.ETERNITY
        default_value = 0

    for var in [salary, is_female, is_student, household_id, household_role]:
        tbs.add_variable(var)

    sim = SimulationBuilder().build_default_simulation(tbs, count=6)
    sim.set_input("household_id", "2024", [0, 0, 0, 1, -1, -1])
    sim.set_input("household_role", "2024", [0, 1, 1, 0, 0, 0])
    sim.set_input("salary", "2024", [1000.0, -200.0, 300.0, 5000.0, 99.0, 99.0])
    sim.set_input("is_female", "2024", [True, False, True, False, True, False])
    sim.set_input("is_student", "2024", [False, True, True, False, False, False])

    return sim


# ──────────────────────────────────────────────────────────────
# 1. Combined role + condition (the bug that was fixed)
# ──────────────────────────────────────────────────────────────


class TestRoleAndConditionCombined:
    """Verify that role and condition filters compose correctly."""

    def test_sum_role_and_condition(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        is_female = rich_sim.calculate("is_female", "2024")

        # Sum salary of children (role=1) who are female
        # hh 0: person 2 (role 1, F, 300) → 300
        # hh 1: nobody → 0
        # Others: 0
        res = link.sum("salary", "2024", role=1, condition=is_female)
        expected = [300.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        numpy.testing.assert_array_almost_equal(res, expected)

    def test_count_role_and_condition(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        is_female = rich_sim.calculate("is_female", "2024")

        # Count children (role=1) who are female
        # hh 0: person 2 → 1
        # hh 1: nobody → 0
        res = link.count("2024", role=1, condition=is_female)
        expected = [1, 0, 0, 0, 0, 0]
        numpy.testing.assert_array_equal(res, expected)

    def test_avg_role_and_condition(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        is_female = rich_sim.calculate("is_female", "2024")

        # Average salary of children (role=1) who are female
        # hh 0: person 2 (300) → avg = 300
        # hh 1: nobody → 0 (division by zero guarded)
        res = link.avg("salary", "2024", role=1, condition=is_female)
        expected = [300.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        numpy.testing.assert_array_almost_equal(res, expected)

    def test_min_role_and_condition(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        is_student = rich_sim.calculate("is_student", "2024")

        # Min salary of children (role=1) who are students
        # hh 0: person 1 (-200, student), person 2 (300, student) → min = -200
        # hh 1: none → 0
        res = link.min("salary", "2024", role=1, condition=is_student)
        expected = [-200.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        numpy.testing.assert_array_almost_equal(res, expected)

    def test_max_role_and_condition(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        is_student = rich_sim.calculate("is_student", "2024")

        # Max salary of children (role=1) who are students
        # hh 0: person 1 (-200), person 2 (300) → max = 300
        res = link.max("salary", "2024", role=1, condition=is_student)
        expected = [300.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        numpy.testing.assert_array_almost_equal(res, expected)

    def test_any_role_and_condition(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        is_female = rich_sim.calculate("is_female", "2024")

        # Any child (role=1) female?
        # hh 0: person 2 (child, F) → True
        # hh 1: no children → False
        res = link.any("is_female", "2024", role=1, condition=is_female)
        expected = [True, False, False, False, False, False]
        numpy.testing.assert_array_equal(res, expected)

    def test_all_role_and_condition(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        is_student = rich_sim.calculate("is_student", "2024")

        # All children (role=1) students?
        # hh 0: person 1 (student=T), person 2 (student=T) → True
        # hh 1: no matching members → True (vacuously true)
        res = link.all("is_student", "2024", role=1, condition=is_student)
        # After filtering by role=1 AND condition=is_student, the remaining
        # members all have is_student=True by construction.
        # But hh 1 has no such members → stays True (vacuously true)
        expected = [True, True, True, True, True, True]
        numpy.testing.assert_array_equal(res, expected)


# ──────────────────────────────────────────────────────────────
# 2. Edge cases for aggregation logic
# ──────────────────────────────────────────────────────────────


class TestAggregationEdgeCases:
    """Edge cases: empty groups, negative values, single-member groups."""

    def test_sum_with_negative_values(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        res_sum = link.sum("salary", "2024")
        # hh 0: 1000 + (-200) + 300 = 1100
        # hh 1: 5000
        # hh 2+: 0
        assert res_sum[0] == pytest.approx(1100.0)
        assert res_sum[1] == pytest.approx(5000.0)
        assert res_sum[2] == pytest.approx(0.0)

    def test_min_with_negative_values(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        res_min = link.min("salary", "2024")
        # hh 0: min(1000, -200, 300) = -200
        # hh 1: 5000
        # hh 2: 0 (empty → sentinel replaced to 0)
        assert res_min[0] == pytest.approx(-200.0)
        assert res_min[1] == pytest.approx(5000.0)
        assert res_min[2] == pytest.approx(0.0)

    def test_max_with_negative_values(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        res_max = link.max("salary", "2024")
        # hh 0: max(1000, -200, 300) = 1000
        # hh 1: 5000
        # hh 2: 0 (empty → sentinel replaced to 0)
        assert res_max[0] == pytest.approx(1000.0)
        assert res_max[1] == pytest.approx(5000.0)
        assert res_max[2] == pytest.approx(0.0)

    def test_avg_empty_household(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        res_avg = link.avg("salary", "2024")
        # hh 2: empty → 0 (division by zero guarded)
        assert res_avg[2] == pytest.approx(0.0)

    def test_avg_single_member_household(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        res_avg = link.avg("salary", "2024")
        # hh 1: single member with salary 5000 → avg = 5000
        assert res_avg[1] == pytest.approx(5000.0)

    def test_avg_multi_member_household(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        res_avg = link.avg("salary", "2024")
        # hh 0: (1000 + (-200) + 300) / 3 ≈ 366.67
        assert res_avg[0] == pytest.approx(1100.0 / 3.0)

    def test_count_empty_household(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        res_count = link.count("2024")
        # hh 2: 0 members
        assert res_count[2] == 0

    def test_count_single_member_household(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        res_count = link.count("2024")
        # hh 1: 1 member
        assert res_count[1] == 1

    def test_all_empty_household_is_vacuously_true(self, rich_sim):
        """For empty groups, `all()` returns True (vacuous truth)."""
        link = rich_sim.populations["household"].links["members"]
        res_all = link.all("is_female", "2024")
        # hh 2: empty → all() returns True by convention
        assert res_all[2] is numpy.bool_(True)

    def test_any_empty_household_is_false(self, rich_sim):
        """For empty groups, `any()` returns False."""
        link = rich_sim.populations["household"].links["members"]
        res_any = link.any("is_female", "2024")
        # hh 2: empty → any() returns False
        assert res_any[2] is numpy.bool_(False)


# ──────────────────────────────────────────────────────────────
# 3. Condition-only filters (no role)
# ──────────────────────────────────────────────────────────────


class TestConditionOnlyFilters:
    """Test condition filter without role."""

    def test_count_with_condition(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        is_female = rich_sim.calculate("is_female", "2024")
        res = link.count("2024", condition=is_female)
        # hh 0: person 0 (F), person 2 (F) → 2
        # hh 1: person 3 (M) → 0
        expected = [2, 0, 0, 0, 0, 0]
        numpy.testing.assert_array_equal(res, expected)

    def test_min_with_condition(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        is_female = rich_sim.calculate("is_female", "2024")
        res = link.min("salary", "2024", condition=is_female)
        # hh 0: min(1000, 300) = 300 (only females)
        assert res[0] == pytest.approx(300.0)
        assert res[1] == pytest.approx(0.0)  # no females in hh 1

    def test_max_with_condition(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        is_female = rich_sim.calculate("is_female", "2024")
        res = link.max("salary", "2024", condition=is_female)
        # hh 0: max(1000, 300) = 1000 (only females)
        assert res[0] == pytest.approx(1000.0)
        assert res[1] == pytest.approx(0.0)  # no females in hh 1

    def test_avg_with_condition(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        is_female = rich_sim.calculate("is_female", "2024")
        res = link.avg("salary", "2024", condition=is_female)
        # hh 0: (1000 + 300) / 2 = 650
        assert res[0] == pytest.approx(650.0)
        # hh 1: no females → 0
        assert res[1] == pytest.approx(0.0)


# ──────────────────────────────────────────────────────────────
# 4. Role-only filters (no condition)
# ──────────────────────────────────────────────────────────────


class TestRoleOnlyFilters:
    """Test role filter without condition."""

    def test_sum_parents_only(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        res = link.sum("salary", "2024", role=0)
        # hh 0: person 0 (role 0, 1000) → 1000
        # hh 1: person 3 (role 0, 5000) → 5000
        assert res[0] == pytest.approx(1000.0)
        assert res[1] == pytest.approx(5000.0)

    def test_sum_children_only(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        res = link.sum("salary", "2024", role=1)
        # hh 0: person 1 (-200) + person 2 (300) = 100
        # hh 1: none → 0
        assert res[0] == pytest.approx(100.0)
        assert res[1] == pytest.approx(0.0)

    def test_count_nonexistent_role(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        # Role 99 doesn't exist — count should be 0 everywhere
        res = link.count("2024", role=99)
        numpy.testing.assert_array_equal(res, [0, 0, 0, 0, 0, 0])

    def test_any_parents_female(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        # Any parent female?
        # hh 0: person 0 (parent, F) → True
        # hh 1: person 3 (parent, M) → False
        res = link.any("is_female", "2024", role=0)
        assert res[0] is numpy.bool_(True)
        assert res[1] is numpy.bool_(False)

    def test_min_max_single_member_role(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        # For a single-member group with the matching role, min == max == value
        res_min = link.min("salary", "2024", role=0)
        res_max = link.max("salary", "2024", role=0)
        # hh 1: person 3 only parent → min = max = 5000
        assert res_min[1] == pytest.approx(5000.0)
        assert res_max[1] == pytest.approx(5000.0)


# ──────────────────────────────────────────────────────────────
# 5. Cross-check: sum == count * avg (when count > 0)
# ──────────────────────────────────────────────────────────────


class TestCrossChecks:
    """Verify mathematical relationships between aggregation methods."""

    def test_sum_equals_count_times_avg(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        s = link.sum("salary", "2024")
        c = link.count("2024")
        a = link.avg("salary", "2024")

        for i in range(len(s)):
            if c[i] > 0:
                assert s[i] == pytest.approx(c[i] * a[i])

    def test_min_le_avg_le_max(self, rich_sim):
        link = rich_sim.populations["household"].links["members"]
        mn = link.min("salary", "2024")
        a = link.avg("salary", "2024")
        mx = link.max("salary", "2024")
        c = link.count("2024")

        for i in range(len(mn)):
            if c[i] > 0:
                assert mn[i] <= a[i] + 1e-10
                assert a[i] <= mx[i] + 1e-10

    def test_sum_with_role_and_condition_equals_filtered_sum(self, rich_sim):
        """Sum with filters == sum of manually filtered values."""
        link = rich_sim.populations["household"].links["members"]
        is_female = rich_sim.calculate("is_female", "2024")

        # Via link
        link_sum = link.sum("salary", "2024", role=1, condition=is_female)

        # Manual computation
        salaries = rich_sim.calculate("salary", "2024")
        hh_ids = rich_sim.calculate("household_id", "2024")
        roles = rich_sim.calculate("household_role", "eternity")
        n_hh = rich_sim.populations["household"].count

        manual_sum = numpy.zeros(n_hh)
        for p in range(len(salaries)):
            hh = hh_ids[p]
            if hh >= 0 and hh < n_hh and roles[p] == 1 and is_female[p]:
                manual_sum[hh] += salaries[p]

        numpy.testing.assert_array_almost_equal(link_sum[:n_hh], manual_sum)
