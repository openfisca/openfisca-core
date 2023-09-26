from openfisca_core import entities


def test_init_when_doc_indented():
    """De-indents the ``doc`` attribute if it is passed at initialisation."""

    key = "\tkey"
    doc = "\tdoc"
    entity = entities.Entity(key, "label", "plural", doc)
    assert entity.key == key
    assert entity.doc != doc
