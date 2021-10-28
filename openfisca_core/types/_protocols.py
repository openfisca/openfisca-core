from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence
from typing_extensions import Protocol
from ._data_types import ArrayType

import abc


class EntityType(Protocol):
    """Duck-type for entities.

    .. versionadded:: 35.8.0

    """

    key: str
    plural: str
    is_person: bool
    flattened_roles: Sequence[RoleType]


class HolderType(Protocol):
    """Duck-type for holders.

    .. versionadded:: 35.8.0

    """

    @abc.abstractmethod
    def create_disk_storage(
            self,
            directory: Optional[str] = ...,
            preserve: bool = ...,
            ) -> StorageType:
        ...

    @abc.abstractmethod
    def put_in_cache(self, value: ArrayType[Any], period: PeriodType) -> None:
        ...

    @abc.abstractmethod
    def get_array(self, period: PeriodType) -> Any:
        ...

    @abc.abstractmethod
    def get_known_periods(self) -> Sequence[PeriodType]:
        ...


class PeriodType(Protocol):
    """Duck-type for periods.

    .. versionadded:: 35.8.0

    """


class PopulationType(Protocol):
    """Duck-type for populations.

    .. versionadded:: 35.8.0

    """

    _holders: Mapping[str, HolderType]
    count: Optional[int]
    entity: EntityType
    ids: Sequence[str]
    members_entity_id: ArrayType[int]
    members_position: ArrayType[int]
    members_role: ArrayType[RoleType]


class RoleType(Protocol):
    """Duck-type for roles.

    .. versionadded:: 35.8.0

    """

    key: str


class StorageType(Protocol):
    """Duck-type for storage mechanisms.

    .. versionadded:: 35.8.0

    """

    @abc.abstractmethod
    def put(self, value: ArrayType[Any], period: PeriodType) -> None:
        ...


class TaxBenefitSystemType(Protocol):
    """Duck-type for tax-benefit systems.

    .. versionadded:: 35.8.0

    """

    person_entity: EntityType

    @abc.abstractmethod
    def apply_reform(self, reform_path: str) -> TaxBenefitSystemType:
        ...

    @abc.abstractmethod
    def clone(self) -> TaxBenefitSystemType:
        ...

    @abc.abstractmethod
    def get_package_metadata(self) -> Mapping[str, str]:
        ...

    @abc.abstractmethod
    def get_variable(
            self,
            variable_name: str,
            check_existence: bool = ...,
            ) -> Optional[VariableType]:
        ...

    @abc.abstractmethod
    def instantiate_entities(self) -> Mapping[str, PopulationType]:
        ...

    @abc.abstractmethod
    def load_extension(self, extension: str) -> None:
        ...


class VariableType(Protocol):
    """Duck-type for variables.

    .. versionadded:: 35.8.0

    """

    definition_period: str
