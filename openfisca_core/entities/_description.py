from __future__ import annotations

import dataclasses
import textwrap


@dataclasses.dataclass(frozen=True)
class Description:
    """A description.

    Examples:
        >>> data = {
        ...     "key": "parent",
        ...     "label": "Parents",
        ...     "plural": "parents",
        ...     "doc": "\t\t\tThe one/two adults in charge of the household.",
        ... }

        >>> description = Description(**data)

        >>> repr(Description)
        "<class 'openfisca_core.entities._description.Description'>"

        >>> repr(description)
        "Description(key='parent', plural='parents', label='Parents', ...)"

        >>> str(description)
        "Description(key='parent', plural='parents', label='Parents', ...)"

        >>> {description}
        {Description(key='parent', plural='parents', label='Parents', doc=...}

        >>> description.key
        'parent'

    .. versionadded:: 41.0.1

    """

    #: A key to identify an entity.
    key: str

    #: The ``key``, pluralised.
    plural: str | None = None

    #: A summary description.
    label: str | None = None

    #: A full description, non-indented.
    doc: str | None = None

    def __post_init__(self) -> None:
        if self.doc is not None:
            object.__setattr__(self, "doc", textwrap.dedent(self.doc))
