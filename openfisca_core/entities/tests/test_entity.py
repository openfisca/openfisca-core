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


def test_init_when_doc_indented():
    """Dedents the ``doc`` attribute if it is passed at initialisation."""

    key = "\tkey"
    doc = "\tdoc"
    entity = Entity(key, "label", "plural", doc)
    assert entity.key == key
    assert entity.doc != doc


def test_set_tax_benefit_system_deprecation(entity):
    """Throws a deprecation warning when called."""

    with pytest.warns(DeprecationWarning):
        entity.set_tax_benefit_system(TaxBenefitSystem([entity]))


def test_check_role_validity_deprecation(entity, role):
    """Throws a deprecation warning when called."""

    with pytest.warns(DeprecationWarning):
        entity.check_role_validity(role)


def test_check_variable_defined_for_entity_deprecation(entity):
    """Throws a deprecation warning when called."""

    with pytest.warns(DeprecationWarning):
        entity.check_variable_defined_for_entity(object())


def test_get_variable_deprecation(entity):
    """Throws a deprecation warning when called."""

    with pytest.warns(DeprecationWarning):
        entity.get_variable("variable")
