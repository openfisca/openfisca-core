"""Tests for members_position vectorized computation."""

import numpy

from openfisca_core.populations.membership import positions, Membership


class TestMembersPosition:
    """Verify that members_position computes the correct intra-entity index."""

    def test_simple_two_entities(self):
        """Two entities with 2 and 3 members."""
        members_entity_id = numpy.array([0, 0, 1, 1, 1])
        result = positions(members_entity_id)
        expected = numpy.array([0, 1, 0, 1, 2])
        numpy.testing.assert_array_equal(result, expected)

    def test_single_entity(self):
        """All persons belong to one entity."""
        members_entity_id = numpy.array([0, 0, 0, 0])
        result = positions(members_entity_id)
        expected = numpy.array([0, 1, 2, 3])
        numpy.testing.assert_array_equal(result, expected)

    def test_one_person_per_entity(self):
        """Each person is in its own entity."""
        members_entity_id = numpy.array([0, 1, 2, 3])
        result = positions(members_entity_id)
        expected = numpy.array([0, 0, 0, 0])
        numpy.testing.assert_array_equal(result, expected)

    def test_non_contiguous_entity_ids(self):
        """Persons from same entity are not contiguous in the array."""
        members_entity_id = numpy.array([0, 1, 0, 1, 0, 1])
        result = positions(members_entity_id)
        expected = numpy.array([0, 0, 1, 1, 2, 2])
        numpy.testing.assert_array_equal(result, expected)

    def test_large_population(self):
        """Stress test with a large population to verify correctness."""
        rng = numpy.random.default_rng(42)
        nb_persons = 100_000
        nb_entities = 40_000
        entity_ids = rng.integers(0, nb_entities, size=nb_persons)
        members_entity_id = entity_ids
        result = positions(members_entity_id)

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
        membership = Membership(None, None, None)
        membership.members_entity_id = numpy.array([0, 0, 1])

        first = membership.members_position
        second = membership.members_position
        assert first is second  # Same object, not recomputed

    def test_dtype_is_int32(self):
        """Result should be int32 for consistency."""
        membership = Membership(None, None, None)
        membership.members_entity_id = numpy.array([0, 0, 1])
        result = membership.members_position
        assert result.dtype == numpy.int32
