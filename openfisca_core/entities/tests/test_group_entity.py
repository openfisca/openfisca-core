import pytest

from openfisca_core.entities import Entity, GroupEntity
from openfisca_core.taxbenefitsystems import TaxBenefitSystem


@pytest.fixture
def roles():
    """A role-like."""

    return [{"key": "parent", "subroles": ["first_parent", "second_parent"]}]


@pytest.fixture
def entity():
    """An entity."""

    return Entity("key", "label", "plural", "doc")


@pytest.fixture
def group_entity(roles):
    """A group entity."""

    return GroupEntity("key", "label", "plural", "doc", roles)


def test_init_when_doc_indented():
    """Dedents the ``doc`` attribute if it is passed at initialisation."""

    key = "\tkey"
    doc = "\tdoc"
    group_entity = GroupEntity(key, "label", "plural", doc, [])
    assert group_entity.key == key
    assert group_entity.doc != doc


def test_set_tax_benefit_system_deprecation(entity, group_entity):
    """Throws a deprecation warning when called."""

    tbs = TaxBenefitSystem([entity, group_entity])

    with pytest.warns(DeprecationWarning):
        group_entity.set_tax_benefit_system(tbs)


def test_check_role_validity_deprecation(group_entity):
    """Throws a deprecation warning when called."""

    with pytest.warns(DeprecationWarning):
        group_entity.check_role_validity(group_entity.PARENT)


def test_check_variable_defined_for_entity_deprecation(group_entity):
    """Throws a deprecation warning when called."""

    with pytest.warns(DeprecationWarning):
        group_entity.check_variable_defined_for_entity(object())


def test_get_variable_deprecation(group_entity):
    """Throws a deprecation warning when called."""

    with pytest.warns(DeprecationWarning):
        group_entity.get_variable("variable")


def test_group_entity_with_roles(group_entity):
    """Assigns a :obj:`.Role` for each role-like passed as argument."""

    assert group_entity.PARENT


def test_group_entity_with_subroles(group_entity):
    """Assigns a :obj:`.Role` for each subrole-like passed as argument."""

    assert group_entity.FIRST_PARENT
