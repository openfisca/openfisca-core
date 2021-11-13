import pytest

from openfisca_core.entities import GroupEntity


@pytest.fixture
def roles():
    """A role-like."""

    return [{"key": "parent", "subroles": ["first_parent", "second_parent"]}]


@pytest.fixture
def group_entity(roles):
    """A group entity."""

    return GroupEntity("key", "label", "plural", "doc", roles)


def test_init_when_doc_indented():
    """Unindents the ``doc`` attribute if it is passed at initialisation."""

    key = "\tkey"
    doc = "\tdoc"
    group_entity = GroupEntity(key, "label", "plural", doc, [])
    assert group_entity.key == key
    assert group_entity.doc != doc


def test_group_entity_with_roles(group_entity):
    """Assigns a :obj:`.Role` for each role-like passed as argument."""

    assert group_entity.PARENT

    with pytest.raises(AttributeError):
        assert group_entity.CHILD


def test_group_entity_with_subroles(group_entity):
    """Assigns a :obj:`.Role` for each subrole-like passed as argument."""

    assert group_entity.FIRST_PARENT

    with pytest.raises(AttributeError):
        assert group_entity.FIRST_CHILD
