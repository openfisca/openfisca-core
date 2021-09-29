from typing import Any

from typing_extensions import Protocol


class Aggregatable(Protocol):
    """Base type for any model implementing population-like behaviour.

    Type-checking against abstractions rather than implementations helps in
    (a) decoupling the codebse, thanks to structural subtyping, and
    (b) documenting/enforcing the blueprints of the different OpenFisca models.

    .. versionadded:: 35.5.0

    """

    count: int
    simulation: Any

    ...
