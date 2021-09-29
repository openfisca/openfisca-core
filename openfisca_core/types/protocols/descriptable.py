from typing import Any, Callable, Optional, Type, TypeVar

from typing_extensions import Protocol

T = TypeVar("T")
F = Callable[..., Optional[T]]


class Descriptable(Protocol[T]):
    """Base type for any model implementing a descriptor protocol.

    Type-checking against abstractions rather than implementations helps in
    (a) decoupling the codebse, thanks to structural subtyping, and
    (b) documenting/enforcing the blueprints of the different OpenFisca models.

    .. versionadded:: 35.5.0

    """

    public_name: str
    private_name: str

    def __get__(self, obj: Any, type: Type[Any]) -> Optional[F[T]]:
        ...

    def __set__(self, obj: Any, value: F[T]) -> None:
        ...
