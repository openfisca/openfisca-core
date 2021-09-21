import abc
from typing import Any

from typing_extensions import Protocol


class SupportsEncode(Protocol):
    """Base type for any model implementing a literal list of choices.

    Type-checking against abstractions rather than implementations helps in
    (a) decoupling the codebse, thanks to structural subtyping, and
    (b) documenting/enforcing the blueprints of the different OpenFisca models.

    .. versionadded:: 35.8.0

    """

    @classmethod
    @abc.abstractmethod
    def encode(cls, array: Any) -> Any:
        """A concrete encodable model implements :meth:`.encode`."""

        ...
