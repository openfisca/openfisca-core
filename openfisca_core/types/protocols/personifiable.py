import abc
from typing import Any

import typing_extensions
from typing_extensions import Protocol

from .descriptable import Descriptable
from ._documentable import Documentable


@typing_extensions.runtime_checkable
class Personifiable(Documentable, Protocol):
    """Base type for any entity-like model.

    Type-checking against abstractions rather than implementations helps in
    (a) decoupling the codebse, thanks to structural subtyping, and
    (b) documenting/enforcing the blueprints of the different OpenFisca models.

    .. versionadded:: 35.5.0

    """

    key: str
    plural: str
    label: str
    doc: str
    is_person: bool
    variable: Descriptable[Any]

    @abc.abstractmethod
    def __init__(self, key: str, plural: str, label: str, doc: str) -> None:
        ...
