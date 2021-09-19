import functools
import warnings
import typing
from typing import Any, Callable, TypeVar

T = Callable[..., Any]
F = TypeVar("F", bound = T)


class deprecated:
    """Allows (soft) deprecating a functionality of OpenFisca.

    Attributes:
        since (:obj:`str`): Since when the functionality is deprecated.
        expires (:obj:`str`): When will it be removed forever?

    Args:
        since: Since when the functionality is deprecated.
        expires: When will it be removed forever?

    Examples:
        >>> @deprecated(since = "35.5.0", expires = "in the future")
        ... def obsolete():
        ...     return "I'm obsolete!"

        >>> repr(obsolete)
        '<function obsolete ...>'

        >>> str(obsolete)
        '<function obsolete ...>'

    .. versionadded:: 35.6.0

    """

    since: str
    expires: str

    def __init__(self, since: str, expires: str) -> None:
        self.since = since
        self.expires = expires

    def __call__(self, function: F) -> F:
        """Wraps a function to return another one, decorated.

        Args:
            function: The function or method to decorate.

        Returns:
            :obj:`callable`: The decorated function.

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

        def wrapper(*args: Any, **kwds: Any) -> Any:
            message = [
                f"{function.__qualname__} has been deprecated since",
                f"version {self.since}, and will be removed in",
                f"{self.expires}.",
                ]
            warnings.warn(" ".join(message), DeprecationWarning)
            return function(*args, **kwds)

        functools.update_wrapper(wrapper, function)
        return typing.cast(F, wrapper)
