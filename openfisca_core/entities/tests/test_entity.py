import pytest

from openfisca_core.entities import Entity, Role
from openfisca_core.taxbenefitsystems import TaxBenefitSystem


@pytest.fixture
def entity():
    """An entity."""
    return Entity("key", "label", "plural", "doc")


@pytest.fixture
def role(entity):
    """A role."""
    return Role({"key": "key"}, entity)


def test_variable_when_not_set(entity):
    """Returns None when not yet defined."""

    assert not entity.variable


def test_variable_query_when_not_set(entity):
    """Raises an exceptions when called and not yet defined."""

    with pytest.raises(TypeError):
        entity.variable("variable")


def test_set_tax_benefit_system_deprecation(entity):
    """:meth:`.set_tax_benefit_system` throws a deprecation warning."""

    with pytest.warns(DeprecationWarning):
        entity.set_tax_benefit_system(TaxBenefitSystem([entity]))


def test_check_role_validity_deprecation(entity, role):
    """:meth:`.check_role_validity` throws a deprecation warning."""

    with pytest.warns(DeprecationWarning):
        entity.check_role_validity(role)


def test_get_variable_deprecation(entity):
    """:meth:`.get_variable` throws a deprecation warning."""

    with pytest.warns(DeprecationWarning):
        entity.get_variable("variable")
