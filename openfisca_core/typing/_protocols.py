# pylint: disable=missing-function-docstring

from __future__ import annotations

from typing import Any, Optional, Sequence
from typing_extensions import Protocol, runtime_checkable

import abc


class EntityProtocol(Protocol):
    """Duck-type for entities.

    .. versionadded:: 35.8.0

    """

    key: str
    plural: str


class FormulaProtocol(Protocol):
    """Duck-type for formulas.

    .. versionadded:: 35.8.0

    """


class GroupEntityProtocol(EntityProtocol, Protocol):
    """Duck-type for group entities.

    .. versionadded:: 35.8.0

    """

    roles: Sequence[RoleProtocol]
    roles_description: Sequence[Any]
    flattened_roles: Sequence[RoleProtocol]


@runtime_checkable
class RoleProtocol(Protocol):
    """Duck-type for roles.

    .. versionadded:: 35.8.0

    """

    key: str
    max: Optional[int]
    subroles: Optional[Sequence[RoleProtocol]]


class TaxBenefitSystemProtocol(Protocol):
    """Duck-type for tax-benefit systems.

    .. versionadded:: 35.8.0

    """

    @abc.abstractmethod
    def get_variable(self, __arg1: str, __arg2: bool = False) -> Optional[Any]:
        ...


class VariableProtocol(Protocol):
    """Duck-type for variables.

    .. versionadded:: 35.8.0

    """
