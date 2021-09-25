import functools
import warnings
import typing
from typing import Any, Callable, Sequence, TypeVar

T = Callable[..., Any]
F = TypeVar("F", bound = T)


class deprecated:
    """Allows (soft) deprecating a functionality of OpenFisca.

    Attributes:
        since:
            Since when the functionality is deprecated.
        expires:
            When will it be removed forever?

    Args:
        since:
            Since when the functionality is deprecated.
        expires:
            When will it be removed forever? Note that this value, if set to a
            valid semantic version, it has to be a major one.

    Raises:
        ValueError:
            When :attr:`expires` is set to a version, but not to a major one.


    Examples:
        >>> @deprecated(since = "35.5.0", expires = "in the future")
        ... def obsolete():
        ...     return "I'm obsolete!"

        >>> repr(obsolete)
        '<function obsolete ...>'

        >>> str(obsolete)
        '<function obsolete ...>'

    .. versionadded:: 36.0.0

    """

    since: str
    expires: str

    def __init__(self, *, since: str, expires: str) -> None:
        self.since = since
        self.expires = self._parse(expires)

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
            message: Sequence[str]
            message = [
                f"{function.__qualname__} has been deprecated since",
                f"version {self.since}, and will be removed in",
                f"{self.expires}.",
                ]

            warnings.warn(" ".join(message), DeprecationWarning)
            return function(*args, **kwds)

        functools.update_wrapper(wrapper, function)
        return typing.cast(F, wrapper)

    @staticmethod
    def _parse(expires: str) -> str:
        minor: str
        patch: str
        message: Sequence[str]

        if expires.find(".") == -1:
            return expires

        _, minor, patch, *_ = expires.split(".")

        if minor != "0" or patch != "0":
            message = [
                "Deprecations can only expire on major releases.",
                f"Or, {expires} is not a major one.",
                "To learn more about semantic versioning:",
                "https://semver.org/"
                ]

            raise ValueError(" ".join(message))

        return expires
