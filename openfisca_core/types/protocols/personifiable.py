import abc
from typing import Any, Iterator, Tuple

import typing_extensions
from typing_extensions import Protocol

from ._documentable import Documentable
from .modellable import Modellable
from .representable import Representable

T = Representable
V = Modellable


@typing_extensions.runtime_checkable
class Personifiable(Documentable, Protocol):
    """Base type for any entity-like model.

    Type-checking against abstractions rather than implementations helps in
    (a) decoupling the codebse, thanks to structural subtyping, and
    (b) documenting/enforcing the blueprints of the different OpenFisca models.

    .. versionadded:: 35.7.0

    """

    plural: str

    @abc.abstractmethod
    def __repr__(self) -> str:
        ...

    @abc.abstractmethod
    def __str__(self) -> str:
        ...

    @abc.abstractmethod
    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        ...
