from __future__ import annotations

import abc
from typing import Iterable, Sequence, Type, TypeVar

from typing_extensions import Protocol

RT = TypeVar("RT", covariant = True)
ET = TypeVar("ET", covariant = True)
EL = TypeVar("EL", contravariant = True)


class Builder(Protocol[RT, ET, EL]):
    """Base type for any model implementing a builder protocol.

    Type-checking against abstractions rather than implementations helps in
    (a) decoupling the codebse, thanks to structural subtyping, and
    (b) documenting/enforcing the blueprints of the different OpenFisca models.

    .. versionadded:: 35.7.0

    """

    @abc.abstractmethod
    def __init__(self, __builder: RT, __buildee: Type[ET]) -> None:
        ...

    @abc.abstractmethod
    def __call__(self, __items: Iterable[EL]) -> Sequence[ET]:
        """A concrete builder implements :meth:`.__call__`."""

        ...

    @abc.abstractmethod
    def build(self, __item: EL) -> ET:
        """A concrete builder implements :meth:`.build`."""

        ...
