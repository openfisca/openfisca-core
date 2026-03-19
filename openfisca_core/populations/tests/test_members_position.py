"""Tests for GroupPopulation.members_position vectorized computation."""

import numpy
import pytest

from openfisca_core import entities, periods, taxbenefitsystems, variables
from openfisca_core.simulations import SimulationBuilder


class TestMembersPosition:
    """Verify that members_position computes the correct intra-entity index."""

    def test_simple_two_entities(self):
        """Two entities with 2 and 3 members."""
        from openfisca_core.populations.group_population import GroupPopulation

        pop = GroupPopulation.__new__(GroupPopulation)
        #  person:     0  1  2  3  4
        #  entity_id: [0, 0, 1, 1, 1]
        #  expected:  [0, 1, 0, 1, 2]
        pop._members_entity_id = numpy.array([0, 0, 1, 1, 1])
        pop._members_position = None
        pop._ordered_members_map = None

        result = pop.members_position
        expected = numpy.array([0, 1, 0, 1, 2])
        numpy.testing.assert_array_equal(result, expected)

    def test_single_entity(self):
        """All persons belong to one entity."""
        from openfisca_core.populations.group_population import GroupPopulation

        pop = GroupPopulation.__new__(GroupPopulation)
        pop._members_entity_id = numpy.array([0, 0, 0, 0])
        pop._members_position = None
        pop._ordered_members_map = None

        result = pop.members_position
        expected = numpy.array([0, 1, 2, 3])
        numpy.testing.assert_array_equal(result, expected)

    def test_one_person_per_entity(self):
        """Each person is in its own entity."""
        from openfisca_core.populations.group_population import GroupPopulation

        pop = GroupPopulation.__new__(GroupPopulation)
        pop._members_entity_id = numpy.array([0, 1, 2, 3])
        pop._members_position = None
        pop._ordered_members_map = None

        result = pop.members_position
        expected = numpy.array([0, 0, 0, 0])
        numpy.testing.assert_array_equal(result, expected)

    def test_non_contiguous_entity_ids(self):
        """Persons from same entity are not contiguous in the array."""
        from openfisca_core.populations.group_population import GroupPopulation

        pop = GroupPopulation.__new__(GroupPopulation)
        #  person:     0  1  2  3  4  5
        #  entity_id: [0, 1, 0, 1, 0, 1]
        #  expected:  [0, 0, 1, 1, 2, 2]
        pop._members_entity_id = numpy.array([0, 1, 0, 1, 0, 1])
        pop._members_position = None
        pop._ordered_members_map = None

        result = pop.members_position
        expected = numpy.array([0, 0, 1, 1, 2, 2])
        numpy.testing.assert_array_equal(result, expected)

    def test_large_population(self):
        """Stress test with a large population to verify correctness."""
        from openfisca_core.populations.group_population import GroupPopulation

        rng = numpy.random.default_rng(42)
        nb_persons = 100_000
        nb_entities = 40_000
        entity_ids = rng.integers(0, nb_entities, size=nb_persons)

        pop = GroupPopulation.__new__(GroupPopulation)
        pop._members_entity_id = entity_ids
        pop._members_position = None
        pop._ordered_members_map = None

        result = pop.members_position

        # Verify with a reference implementation (the old Python loop)
        expected = numpy.empty(nb_persons, dtype=int)
        counter = numpy.zeros(nb_entities, dtype=int)
        for k in range(nb_persons):
            idx = entity_ids[k]
            expected[k] = counter[idx]
            counter[idx] += 1

        numpy.testing.assert_array_equal(result, expected)

    def test_cached_after_first_call(self):
        """members_position should be cached after first computation."""
        from openfisca_core.populations.group_population import GroupPopulation

        pop = GroupPopulation.__new__(GroupPopulation)
        pop._members_entity_id = numpy.array([0, 0, 1])
        pop._members_position = None
        pop._ordered_members_map = None

        first = pop.members_position
        second = pop.members_position
        assert first is second  # Same object, not recomputed

    def test_dtype_is_int32(self):
        """Result should be int32 for consistency."""
        from openfisca_core.populations.group_population import GroupPopulation

        pop = GroupPopulation.__new__(GroupPopulation)
        pop._members_entity_id = numpy.array([0, 1, 0])
        pop._members_position = None
        pop._ordered_members_map = None

        result = pop.members_position
        assert result.dtype == numpy.int32

    def test_set_members_entity_id_empty_raises(self):
        """set_members_entity_id([]) should raise a clear ValueError."""
        from openfisca_core.populations.group_population import GroupPopulation

        pop = GroupPopulation.__new__(GroupPopulation)
        with pytest.raises(ValueError, match="cannot be empty"):
            pop.set_members_entity_id([])

    def test_set_members_entity_id_non_contiguous_count(self):
        """Non-contiguous ids should be accepted; count is max(id)+1."""
        person = entities.SingleEntity("person", "persons", "A person", "")
        household = entities.GroupEntity(
            "household", "households", "A household", "", roles=[{"key": "member"}]
        )
        tbs = taxbenefitsystems.TaxBenefitSystem([person, household])

        class age(variables.Variable):
            value_type = int
            entity = person
            definition_period = periods.DateUnit.YEAR

        tbs.add_variable(age)

        sim = SimulationBuilder().build_default_simulation(
            tbs,
            count=4,
            group_members={"household": numpy.array([0, 0, 2, 2])},
        )
        sim.set_input("age", "2024", [10, 20, 30, 40])

        assert sim.household.count == 3  # max([0,0,2,2]) + 1

        first = sim.household.value_nth_person(
            0, sim.persons("age", "2024"), default=-1
        )
        second = sim.household.value_nth_person(
            1, sim.persons("age", "2024"), default=-1
        )
        numpy.testing.assert_array_equal(first, [10, -1, 30])
        numpy.testing.assert_array_equal(second, [20, -1, 40])

        ranks = sim.persons.get_rank(sim.household, sim.persons("age", "2024"))
        numpy.testing.assert_array_equal(ranks, [0, 1, 0, 1])
