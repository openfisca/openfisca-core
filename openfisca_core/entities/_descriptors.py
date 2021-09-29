from __future__ import annotations

from typing import Any, Callable, Optional, Type

from openfisca_core.variables import Variable

F = Callable[[str, bool], Optional[Variable]]


class VariableDescriptor:
    """A `descriptor`_ to search for :class:`.Variable <Variables>`.

    Note:
        The main idea of this module is to extract the dependency from
        :class:`.Entity`. However, it may be good also to completly deprecate
        this indirection in the future.

    Examples:
        >>> class Ruleset:
        ...     variable = VariableDescriptor()

        >>> def get_variable(name):
        ...     # ... some logic here
        ...     if name == "this":
        ...         return "This!"

        >>> ruleset = Ruleset()
        >>> ruleset.variable
        >>> ruleset.variable = get_variable
        >>> ruleset.variable("that")
        >>> ruleset.variable("this")
        'This!'

    .. _descriptor: https://docs.python.org/3/howto/descriptor.html

    .. versionadded:: 35.5.0

    """

    public_name: str = "variable"
    private_name: str = "_variable"

    def __get__(self, obj: Any, type: Type[Any]) -> Optional[F]:

        func: Optional[F]
        func = getattr(obj, self.private_name, None)
        return func

    def __set__(self, obj: Any, value: F) -> None:

        setattr(obj, self.private_name, value)
