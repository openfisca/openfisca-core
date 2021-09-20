import abc
from typing import Any, Optional

from typing_extensions import Protocol


class Representable(Protocol):
    """Base type for any ruleset-like model.

    Type-checking against abstractions rather than implementations helps in
    (a) decoupling the codebse, thanks to structural subtyping, and
    (b) documenting/enforcing the blueprints of the different OpenFisca models.

    .. versionadded:: 35.7.0

    """

    @abc.abstractmethod
    def get_variable(self, __arg1: str, __arg2: bool = False) -> Optional[Any]:
        """A concrete representable model implements :meth:`.get_variable`."""

        ...
