from __future__ import annotations

import abc
from typing import Any, Optional, Sequence

from typing_extensions import Protocol


class HasRoles(Protocol):
    """Duck-type for entities.

    .. versionadded:: 35.7.0

    """

    roles: Sequence[SupportsRole]


class HasVariables(Protocol):
    """Duck-type for tax-benefit systems.

    .. versionadded:: 35.7.0

    """

    @abc.abstractmethod
    def get_variable(self, __arg1: str, __arg2: bool = False) -> Optional[Any]:
        """A tax-benefit system implements :meth:`.get_variable`."""


class SupportsRole(Protocol):
    """Duck-type for roles.

    .. versionadded:: 35.7.0

    """

    max: Optional[int]
    subroles: Optional[Sequence[SupportsRole]]
