import textwrap

from . import types as t
from ._core_entity import _CoreEntity


class Entity(_CoreEntity):
    """Represents an entity (e.g. a person, a household, etc.) on which calculations can be run."""

    def __init__(self, key: str, plural: str, label: str, doc: str) -> None:
        self.key = t.EntityKey(key)
        self.label = label
        self.plural = t.EntityPlural(plural)
        self.doc = textwrap.dedent(doc)
        self.is_person = True
