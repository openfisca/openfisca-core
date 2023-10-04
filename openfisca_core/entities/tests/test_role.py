from openfisca_core import entities


class TestEntity:
    @property
    def key(self) -> str:
        return "key"


def test_init_when_doc_indented() -> None:
    """De-indent the ``doc`` attribute if it is passed at initialisation."""
    key = "\tkey"
    doc = "\tdoc"
    role = entities.Role({"key": key, "doc": doc}, TestEntity())
    assert role.key == key
    assert role.doc == doc.lstrip()
