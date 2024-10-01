from typing import ClassVar

import textwrap

from . import types as t
from ._core_entity import _CoreEntity


class Entity(_CoreEntity):
    """An entity (e.g. a person, a household) on which calculations can be run.

    Args:
        key: A key to identify the ``Entity``.
        plural: The ``key`` pluralised.
        label: A summary description.
        doc: A full description.

    """

    #: A key to identify the ``Entity``.
    key: t.EntityKey

    #: The ``key`` pluralised.
    plural: t.EntityPlural

    #: A summary description.
    label: str

    #: A full description.
    doc: str

    #: Whether the ``Entity`` is a person or not.
    is_person: ClassVar[bool] = True

    def __init__(self, key: str, plural: str, label: str, doc: str) -> None:
        self.key = t.EntityKey(key)
        self.plural = t.EntityPlural(plural)
        self.label = label
        self.doc = textwrap.dedent(doc)


__all__ = ["Entity"]
