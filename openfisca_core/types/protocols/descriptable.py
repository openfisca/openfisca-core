from typing import Any, Optional, Type, TypeVar

from typing_extensions import Protocol

T = TypeVar("T", covariant = True)


class Descriptable(Protocol[T]):
    """Base type for any model implementing a descriptor protocol.

    Type-checking against abstractions rather than implementations helps in
    (a) decoupling the codebse, thanks to structural subtyping, and
    (b) documenting/enforcing the blueprints of the different OpenFisca models.

    .. versionadded:: 35.7.0

    """

    def __get__(self, __instance: Any, __owner: Type[Any]) -> Optional[T]:
        ...

    def __set__(self, __instance: Any, __value: Any) -> None:
        ...
