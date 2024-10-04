from __future__ import annotations

import dataclasses
import textwrap


@dataclasses.dataclass(frozen=True)
class _Description:
    """A ``Role``'s description.

    Examples:
        >>> data = {
        ...     "key": "parent",
        ...     "label": "Parents",
        ...     "plural": "parents",
        ...     "doc": "\t\t\tThe one/two adults in charge of the household.",
        ... }

        >>> description = _Description(**data)

        >>> repr(_Description)
        "<class 'openfisca_core.entities._description._Description'>"

        >>> repr(description)
        "_Description(key='parent', plural='parents', label='Parents', ...)"

        >>> str(description)
        "_Description(key='parent', plural='parents', label='Parents', ...)"

        >>> {description}
        {_Description(key='parent', plural='parents', label='Parents', doc=...}

        >>> description.key
        'parent'

    """

    #: A key to identify the ``Role``.
    key: str

    #: The ``key`` pluralised.
    plural: None | str = None

    #: A summary description.
    label: None | str = None

    #: A full description, non-indented.
    doc: None | str = None

    def __post_init__(self) -> None:
        if self.doc is not None:
            object.__setattr__(self, "doc", textwrap.dedent(self.doc))


__all__ = ["_Description"]
