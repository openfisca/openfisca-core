import abc
from typing import Any, Optional

from typing_extensions import Protocol


class HasHolders(Protocol):
    """Base type for any population-like model.

    Type-checking against abstractions rather than implementations helps in
    (a) decoupling the codebse, thanks to structural subtyping, and
    (b) documenting/enforcing the blueprints of the different OpenFisca models.

    .. versionadded:: 35.7.0

    """

    @abc.abstractmethod
    def get_holder(self, __arg1: str) -> Optional[Any]:
        """A concrete representable model implements :meth:`.get_holder`."""

        ...
