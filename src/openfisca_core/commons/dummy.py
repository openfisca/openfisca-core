import warnings


class Dummy:
    """A class that does nothing."""

    def __init__(self) -> None:
        message = [
            "The 'Dummy' class has been deprecated since version 34.7.0,",
            "and will be removed in the future.",
            ]
        warnings.warn(" ".join(message), DeprecationWarning)
        pass
