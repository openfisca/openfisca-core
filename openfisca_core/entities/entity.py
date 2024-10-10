from typing import ClassVar

import textwrap

from . import types as t
from ._core_entity import CoreEntity


class Entity(CoreEntity):
    r"""An entity (e.g. a person, a household) on which calculations can be run.

    Args:
        key: A key to identify the ``Entity``.
        plural: The ``key`` pluralised.
        label: A summary description.
        doc: A full description.

    Examples:
        >>> from openfisca_core import entities

        >>> entity = entities.SingleEntity(
        ...     "individual",
        ...     "individuals",
        ...     "An individual",
        ...     "\t\t\tThe minimal legal entity on which a rule might be a...",
        ... )

        >>> repr(entities.SingleEntity)
        "<class 'openfisca_core.entities.entity.Entity'>"

        >>> repr(entity)
        'Entity(individual)'

        >>> str(entity)
        'Entity(individual)'

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
