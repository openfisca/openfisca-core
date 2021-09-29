import abc
from typing import Any, Iterable, TypeVar

from typing_extensions import Protocol

T = TypeVar("T", covariant = True)


class Instantizable(Iterable[T], Protocol):
    """Base type for any model implementing a time-based index.

    Type-checking against abstractions rather than implementations helps in
    (a) decoupling the codebse, thanks to structural subtyping, and
    (b) documenting/enforcing the blueprints of the different OpenFisca models.

    .. versionadded:: 35.5.0

    """

    @abc.abstractmethod
    def __getitem__(self, key: Any) -> T:
        ...
