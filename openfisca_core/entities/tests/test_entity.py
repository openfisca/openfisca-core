from openfisca_core.entities import Entity


def test_init_when_doc_indented():
    """Unindents the ``doc`` attribute if it is passed at initialisation."""

    key = "\tkey"
    doc = "\tdoc"
    entity = Entity(key, "label", "plural", doc)
    assert entity.key == key
    assert entity.doc != doc
