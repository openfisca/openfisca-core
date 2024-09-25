from typing import ClassVar

import textwrap

from . import types as t
from ._core_entity import _CoreEntity


class Entity(_CoreEntity):
    """An entity (e.g. a person, a household) on which calculations can be run."""

    #: Whether the entity is a person or not.
    is_person: ClassVar[bool] = True

    def __init__(self, key: str, plural: str, label: str, doc: str) -> None:
        self.key = t.EntityKey(key)
        self.plural = t.EntityPlural(plural)
        self.label = label
        self.doc = textwrap.dedent(doc)


__all__ = ["Entity"]
