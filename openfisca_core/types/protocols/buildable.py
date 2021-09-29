from __future__ import annotations

import abc
from typing import Iterable, Sequence, Type, TypeVar

from typing_extensions import Protocol

RT = TypeVar("RT", covariant = True)
ET = TypeVar("ET", covariant = True)
EL = TypeVar("EL", contravariant = True)


class Buildable(Protocol[RT, ET, EL]):
    """Base type for any model implementing a builder protocol.

    Type-checking against abstractions rather than implementations helps in
    (a) decoupling the codebse, thanks to structural subtyping, and
    (b) documenting/enforcing the blueprints of the different OpenFisca models.

    .. versionadded:: 35.5.0

    """

    @abc.abstractmethod
    def __init__(self, builder: RT, buildee: Type[ET]) -> None:
        ...

    @abc.abstractmethod
    def __call__(self, items: Iterable[EL]) -> Sequence[ET]:
        """A concrete builder implements :meth:`.__call__`."""
        ...

    @abc.abstractmethod
    def build(self, item: EL) -> ET:
        """A concrete builder implements :meth:`.build`."""
        ...
