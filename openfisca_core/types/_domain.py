from __future__ import annotations

import typing
from typing import Any, NoReturn, Optional, Union
from typing_extensions import Protocol

import abc


class Entity(Protocol):
    key: str

    @abc.abstractmethod
    def check_role_validity(self, __arg1: Any) -> None:
        ...

    @abc.abstractmethod
    def check_variable_defined_for_entity(self, __arg1: str) -> None:
        ...


class Holder(Protocol):
    ...


class Period(Protocol):
    ...


class Population(Protocol):
    entity: Any

    @abc.abstractmethod
    def get_holder(self, __arg1: str) -> Any:
        ...


class Role(Protocol):
    entity: Any
    subroles: Any


class Simulation(Protocol):
    ...


class TaxBenefitSystem(Protocol):
    person_entity: Any

    @abc.abstractmethod
    def get_variable(self, __arg1: str, __arg2: bool) -> Optional[Any]:
        ...


class Variable(Protocol):
    entity: Any
