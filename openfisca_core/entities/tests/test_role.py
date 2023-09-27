from typing import Any

import pytest

from openfisca_core import entities

from openfisca_core.entities.typing import Entity


@pytest.fixture
def entity() -> Any:
    """An entity."""

    return object()


def test_init_when_doc_indented(entity: Entity) -> None:
    """De-indent the ``doc`` attribute if it is passed at initialisation."""

    key = "\tkey"
    doc = "\tdoc"
    role = entities.Role({"key": key, "doc": doc}, entity)
    assert role.key == key
    assert role.doc != doc
