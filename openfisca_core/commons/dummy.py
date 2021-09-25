from .decorators import deprecated


class Dummy:
    """A class that did nothing.

    Examples:
        >>> Dummy()
        <openfisca_core.commons.dummy.Dummy object...

    .. deprecated:: 34.7.0
        :class:`.Dummy` has been deprecated and it will be removed in the
        future.

    """

    @deprecated(since = "34.7.0", expires = "36.0.0")
    def __init__(self) -> None:
        ...
