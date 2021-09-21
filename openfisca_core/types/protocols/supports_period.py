from typing_extensions import Protocol


class SupportsPeriod(Protocol):
    """Base type for any model implementing a period/instant-like behaviour.

    Type-checking against abstractions rather than implementations helps in
    (a) decoupling the codebse, thanks to structural subtyping, and
    (b) documenting/enforcing the blueprints of the different OpenFisca models.

    .. versionadded:: 35.7.0

    """

    ...
