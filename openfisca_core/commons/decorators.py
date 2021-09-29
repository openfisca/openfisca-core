import functools
import warnings
import typing
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound = Callable[..., Any])


class deprecated:
    """Allows (soft) deprecating a functionality of OpenFisca.

    Attributes:
        since (:obj:`str`): Since when the functionality is deprecated.
        expires (:obj:`str`): When wil it be removed forever?

    Args:
        since: Since when the functionality is deprecated.
        expires: When wil it be removed forever?

    Examples:
        >>> @deprecated(since = "35.5.0", expires = "in the future")
        ... def obsolete():
        ...     return "I'm obsolete!"

    """

    def __init__(self, since: str, expires: str) -> None:
        self.since = since
        self.expires = expires

    def __call__(self, function: F) -> F:
        """Wraps a function to return another one, decorated.

        Args:
            function: The function or method to decorate.

        Returns:
            The decorated function.

        Examples:
            >>> def obsolete():
            ...     return "I'm obsolete!"

            >>> decorator = deprecated(
            ...     since = "35.5.0",
            ...     expires = "in the future",
            ...     )

            >>> decorator(obsolete)
            <function obsolete ...>

        """

        self.function = function

        def wrapper(*args: Any, **kwds: Any) -> Any:
            message = [
                f"{self.function.__qualname__} has been deprecated since",
                f"version {self.since}, and will be removed in",
                f"{self.expires}.",
                ]
            warnings.warn(" ".join(message), DeprecationWarning)
            return self.function(*args, **kwds)

        functools.update_wrapper(wrapper, function)
        return typing.cast(F, wrapper)
