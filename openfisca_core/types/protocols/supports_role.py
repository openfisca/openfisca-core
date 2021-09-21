from __future__ import annotations

import abc
from typing import Any, Optional, Iterator, Sequence, Tuple

import typing_extensions
from typing_extensions import Protocol

from ..data_types import RoleLike
from ._documentable import Documentable
from .has_plural import HasPlural

R = RoleLike
G = HasPlural


@typing_extensions.runtime_checkable
class SupportsRole(Documentable, Protocol):
    """Base type for any role-like model.

    Type-checking against abstractions rather than implementations helps in
    (a) decoupling the codebse, thanks to structural subtyping, and
    (b) documenting/enforcing the blueprints of the different OpenFisca models.

    .. versionadded:: 35.7.0

    """

    max: Optional[int]
    subroles: Optional[Sequence[SupportsRole]]

    @abc.abstractmethod
    def __repr__(self) -> str:
        ...

    @abc.abstractmethod
    def __str__(self) -> str:
        ...

    @abc.abstractmethod
    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        ...

    @abc.abstractmethod
    def __init__(self, __arg1: R, __arg2: G) -> None:
        ...
