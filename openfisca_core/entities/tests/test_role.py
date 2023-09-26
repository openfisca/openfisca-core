from openfisca_core import entities


def test_init_when_doc_indented() -> None:
    """De-indent the ``doc`` attribute if it is passed at initialisation."""

    key = "\tkey"
    doc = "\tdoc"
    role = entities.Role({"key": key, "doc": doc}, object())
    assert role.key == key
    assert role.doc != doc
