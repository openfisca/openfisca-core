import warnings


class Dummy:
    """A class that did nothing.

    Examples:
        >>> Dummy()
        <openfisca_core.commons.dummy.Dummy object...

    .. deprecated:: 34.7.0
        :class:`.Dummy` has been deprecated and it will be removed in the
        future.

    """

    def __init__(self) -> None:
        message = [
            "The 'Dummy' class has been deprecated since version 34.7.0,",
            "and will be removed in the future.",
            ]
        warnings.warn(" ".join(message), DeprecationWarning)
        pass
