from openfisca_core.entities import Role


def test_init_when_doc_indented():
    """Dedents the ``doc`` attribute if it is passed at initialisation."""

    key = "\tkey"
    doc = "\tdoc"
    role = Role({"key": key, "doc": doc}, object())
    assert role.key == key
    assert role.doc != doc
