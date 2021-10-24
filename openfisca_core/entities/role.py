from __future__ import annotations

from typing import Optional, Sequence
from typing_extensions import TypedDict

import textwrap


class Role:

    def __init__(self, description, entity):
        self.entity = entity
        self.key = description['key']
        self.label = description.get('label')
        self.plural = description.get('plural')
        self.doc = textwrap.dedent(description.get('doc', ""))
        self.max = description.get('max')
        self.subroles = None

    def __repr__(self):
        return "Role({})".format(self.key)


class RoleLike(TypedDict, total = False):
    """Base type for any data castable to a :class:`.Role`.

    .. versionadded:: 35.7.0

    """

    key: str
    plural: Optional[str]
    label: Optional[str]
    doc: Optional[str]
    max: Optional[int]
    subroles: Optional[Sequence[str]]
