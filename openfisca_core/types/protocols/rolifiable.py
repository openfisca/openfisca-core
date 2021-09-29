from __future__ import annotations

import abc
from typing import Optional, Sequence

import typing_extensions
from typing_extensions import Protocol

from ..data_types import RoleLike
from ._documentable import Documentable
from .personifiable import Personifiable


@typing_extensions.runtime_checkable
class Rolifiable(Documentable, Protocol):
    """Base type for any role-like model.

    Type-checking against abstractions rather than implementations helps in
    (a) decoupling the codebse, thanks to structural subtyping, and
    (b) documenting/enforcing the blueprints of the different OpenFisca models.

    .. versionadded:: 35.5.0

    """

    entity: Personifiable
    key: str
    plural: Optional[str]
    label: Optional[str]
    doc: str
    max: Optional[int]
    subroles: Optional[Sequence[Rolifiable]]

    @abc.abstractmethod
    def __init__(self, description: RoleLike, entity: Personifiable) -> None:
        ...
