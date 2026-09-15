from collections.abc import Mapping
from typing import Any

import pytest

from openfisca_core import entities


def test_init_when_doc_indented() -> None:
    """De-indent the ``doc`` attribute if it is passed at initialisation."""
    key = "\tkey"
    doc = "\tdoc"
    entity = entities.Entity(key, "label", "plural", doc)
    assert entity.key == key
    assert entity.doc == doc.lstrip()


@pytest.fixture
def parent() -> str:
    return "parent"


@pytest.fixture
def uncle() -> str:
    return "uncle"


@pytest.fixture
def first_parent() -> str:
    return "first_parent"


@pytest.fixture
def second_parent() -> str:
    return "second_parent"


@pytest.fixture
def third_parent() -> str:
    return "third_parent"


@pytest.fixture
def role(parent: str, first_parent: str, third_parent: str) -> Mapping[str, Any]:
    return {"key": parent, "subroles": {first_parent, third_parent}}


@pytest.fixture
def group_entity(role: Mapping[str, Any]) -> entities.Entity:
    entity = entities.Entity("key", "label", "plural", "doc")
    group_entity = entities.Entity("key", "label", "plural", "doc")
    group_entity.add_relationship(entity, [role])
    return group_entity


def test_init_when_doc_indented() -> None:
    """De-indent the ``doc`` attribute if it is passed at initialisation."""
    entity = entities.Entity("key", "label", "plural", "doc")
    key = "\tkey"
    doc = "\tdoc"
    group_entity = entities.Entity(key, "label", "plural", doc)
    group_entity.add_relationship(entity, [])
    assert group_entity.key == key
    assert group_entity.doc == doc.lstrip()


def test_group_entity_with_roles(
    group_entity: entities.Entity,
    parent: str,
    uncle: str,
) -> None:
    """Assign a Role for each role-like passed as argument."""
    assert hasattr(group_entity, parent.upper())
    assert not hasattr(group_entity, uncle.upper())


def test_group_entity_with_subroles(
    group_entity: entities.Entity,
    first_parent: str,
    second_parent: str,
) -> None:
    """Assign a Role for each subrole-like passed as argument."""
    assert hasattr(group_entity, first_parent.upper())
    assert not hasattr(group_entity, second_parent.upper())
