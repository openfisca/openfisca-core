from openfisca_core import entities


def test_init_when_doc_indented() -> None:
    """De-indent the ``doc`` attribute if it is passed at initialisation."""
    key = "\tkey"
    doc = "\tdoc"
    entity = entities.Entity("key", "plural", "label", "doc")
    group = entities.Entity("key", "plural", "label", "doc")
    group.add_link(entity, [])
    role = entities.Role({"key": key, "doc": doc}, entity)
    assert role.key == key
    assert role.doc == doc.lstrip()
