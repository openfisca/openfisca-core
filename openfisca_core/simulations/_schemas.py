from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union

from pydantic import BaseModel

from openfisca_core.types import Array, Entity, Population


class Axis(BaseModel):
    name: str
    count: int
    min: float
    max: float
    period: Optional[Union[int, str]] = None
    index: int = 0


class EntityCounts(BaseModel):
    __root__: Dict[str, Sequence[int]]

    def __getitem__(self, key: str) -> Sequence[int]:
        return self.__root__[key]

    def __setitem__(self, key: str, value: Sequence[int]) -> None:
        self.__root__[key] = value


class EntityIds(BaseModel):
    __root__: Dict[str, Sequence[int]]

    def __getitem__(self, key: str) -> Sequence[int]:
        return self.__root__[key]

    def __setitem__(self, key: str, value: Sequence[int]) -> None:
        self.__root__[key] = value


class InputBuffer(BaseModel):
    __root__: Dict[str, Dict[str, Array]]

    def __getitem__(self, key: str) -> Dict[str, Array]:
        return self.__root__[key]

    def __setitem__(self, key: str, value: Dict[str, Array]) -> None:
        self.__root__[key] = value

    class Config:
        arbitrary_types_allowed = True


class Memberships(BaseModel):
    __root__: Dict[str, Sequence[int]]

    def __getitem__(self, key: str) -> Sequence[int]:
        return self.__root__[key]

    def __setitem__(self, key: str, value: Sequence[int]) -> None:
        self.__root__[key] = value


class Populations(BaseModel):
    __root__: Dict[str, Population]

    def __getitem__(self, key: str) -> Population:
        return self.__root__[key]

    def __setitem__(self, key: str, value: Population) -> None:
        self.__root__[key] = value

    class Config:
        arbitrary_types_allowed = True


class Roles(BaseModel):
    __root__: Dict[str, Sequence[int]]

    def __getitem__(self, key: str) -> Sequence[int]:
        return self.__root__[key]

    def __setitem__(self, key: str, value: Sequence[int]) -> None:
        self.__root__[key] = value


class VariableEntities(BaseModel):
    __root__: Dict[str, Entity]

    def __getitem__(self, key: str) -> Entity:
        return self.__root__[key]

    def __setitem__(self, key: str, value: Entity) -> None:
        self.__root__[key] = value

    class Config:
        arbitrary_types_allowed = True
