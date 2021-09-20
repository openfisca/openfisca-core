import pytest

from openfisca_core import entities


def test_build_entity_without_roles():
    """Raises a ArgumentError when it's called without roles."""

    with pytest.raises(ValueError):
        entities.build_entity("", "", "", roles = None)


def test_check_role_validity_when_not_role():
    """Raises a ValueError when it gets an invalid role."""

    with pytest.raises(ValueError):
        entities.check_role_validity(object())
