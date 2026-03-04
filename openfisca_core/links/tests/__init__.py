"""Tests for the Link base class."""

from openfisca_core.links.link import Link


class TestLink:
    """Verify Link construction and lifecycle."""

    def test_construction(self):
        link = Link(
            name="household",
            link_field="household_id",
            target_entity_key="household",
        )
        assert link.name == "household"
        assert link.link_field == "household_id"
        assert link.target_entity_key == "household"
        assert link.role_field is None
        assert link.position_field is None

    def test_construction_with_role(self):
        link = Link(
            name="household",
            link_field="household_id",
            target_entity_key="household",
            role_field="household_role",
            position_field="household_position",
        )
        assert link.role_field == "household_role"
        assert link.position_field == "household_position"

    def test_repr(self):
        link = Link(
            name="mother",
            link_field="mother_id",
            target_entity_key="person",
        )
        assert "mother" in repr(link)
        assert "person" in repr(link)

    def test_is_resolved_false_initially(self):
        link = Link(
            name="test",
            link_field="test_id",
            target_entity_key="person",
        )
        assert not link.is_resolved

    def test_resolve_unknown_entity_raises(self):
        link = Link(
            name="test",
            link_field="test_id",
            target_entity_key="unknown",
        )
        import pytest

        with pytest.raises(KeyError, match="unknown"):
            link.resolve({"person": object()})
