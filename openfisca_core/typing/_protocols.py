# pylint: disable=missing-function-docstring

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence, Set, overload
from typing_extensions import Literal, Protocol
from ._types import ArrayType

import abc


class EntityProtocol(Protocol):
    """Duck-type for entities.

    .. versionadded:: 35.8.0

    """

    key: str
    plural: str
    is_person: bool
    flattened_roles: Sequence[RoleProtocol]


class FormulaProtocol(Protocol):
    """Duck-type for formulas"""

    def __call__(
            self,
            __population: PopulationProtocol,
            __period: PeriodProtocol,
            __pararameters: ParametersProtocol,
            ) -> ArrayType[Any]:
        ...


class HolderProtocol(Protocol):
    """Duck-type for holders.

    .. versionadded:: 35.8.0

    """

    @abc.abstractmethod
    def create_disk_storage(
            self,
            directory: Optional[str] = ...,
            preserve: bool = ...,
            ) -> StorageProtocol:
        ...

    @abc.abstractmethod
    def put_in_cache(
            self,
            value: ArrayType[Any],
            period: PeriodProtocol,
            ) -> None:
        ...

    @abc.abstractmethod
    def get_array(self, period: PeriodProtocol) -> Any:
        ...

    @abc.abstractmethod
    def get_known_periods(self) -> Sequence[PeriodProtocol]:
        ...


class InstantProtocol(Protocol):
    """Duck-type for instants.

    .. versionadded:: 35.8.0

    """


class ParameterNodeAtInstantProtocol(Protocol):
    """Duck-type for parameter nodes at instant.

    .. versionadded:: 35.8.0

    """


class ParametersProtocol(Protocol):
    """Duck-type for parameters.

    .. versionadded:: 35.8.0

    """

    def __call__(
            self,
            instant: InstantProtocol,
            ) -> ParameterNodeAtInstantProtocol:
        ...


class PeriodProtocol(Protocol):
    """Duck-type for periods.

    .. versionadded:: 35.8.0

    """


class PopulationProtocol(Protocol):
    """Duck-type for populations.

    .. versionadded:: 35.8.0

    """

    _holders: Mapping[str, HolderProtocol]
    count: Optional[int]
    entity: EntityProtocol
    ids: Sequence[str]
    members_entity_id: ArrayType[int]
    members_position: ArrayType[int]
    members_role: ArrayType[RoleProtocol]

    @abc.abstractmethod
    def get_index(self, id: str) -> int:
        ...


class RoleProtocol(Protocol):
    """Duck-type for roles.

    .. versionadded:: 35.8.0

    """

    key: str


class StorageProtocol(Protocol):
    """Duck-type for storage mechanisms.

    .. versionadded:: 35.8.0

    """

    @abc.abstractmethod
    def put(self, value: ArrayType[Any], period: PeriodProtocol) -> None:
        ...


class TaxBenefitSystemProtocol(Protocol):
    """Duck-type for tax-benefit systems.

    .. versionadded:: 35.8.0

    """

    person_entity: EntityProtocol

    @abc.abstractmethod
    def apply_reform(self, reform_path: str) -> TaxBenefitSystemProtocol:
        ...

    @abc.abstractmethod
    def clone(self) -> TaxBenefitSystemProtocol:
        ...

    @abc.abstractmethod
    def entities_plural(self) -> Set[str]:
        ...

    @abc.abstractmethod
    def get_package_metadata(self) -> Mapping[str, str]:
        ...

    @overload
    def get_variable(
            self,
            variable_name: str,
            check_existence: Literal[True] = ...,
            ) -> VariableProtocol:
        ...

    @overload
    def get_variable(
            self,
            variable_name: str,
            check_existence: bool = ...,
            ) -> Optional[VariableProtocol]:
        ...

    @abc.abstractmethod
    def get_variable(
            self,
            variable_name: str,
            check_existence: bool = ...,
            ) -> Optional[VariableProtocol]:
        ...

    @abc.abstractmethod
    def instantiate_entities(self) -> Mapping[str, PopulationProtocol]:
        ...

    @abc.abstractmethod
    def load_extension(self, extension: str) -> None:
        ...


class VariableProtocol(Protocol):
    """Duck-type for variables.

    .. versionadded:: 35.8.0

    """

    definition_period: str
    name: str
