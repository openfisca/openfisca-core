from __future__ import annotations

import typing
from typing import Any, NoReturn, Optional, Union
from typing_extensions import Protocol

import abc


class Entity(Protocol):
    key: Any

    @abc.abstractmethod
    def check_role_validity(self, __arg1: Any) -> None:
        ...

    @abc.abstractmethod
    def check_variable_defined_for_entity(self, __arg1: Any) -> None:
        ...

    @abc.abstractmethod
    def get_variable(self, __arg1: Any, __arg2: Any = ...) -> Optional[Any]:
        ...


class Holder(Protocol):
    @abc.abstractmethod
    def clone(self, __arg: Any) -> Holder:
        ...

    @abc.abstractmethod
    def get_memory_usage(self) -> Any:
        ...


class Period(Protocol):
    ...


class Population(Protocol):
    entity: Any

    @abc.abstractmethod
    def get_holder(self, __arg1: Any) -> Any:
        ...


class Role(Protocol):
    entity: Any
    subroles: Any


class Simulation(Protocol):
    @abc.abstractmethod
    def calculate(self, __arg1: Any, __arg2: Any) -> Any:
        ...

    @abc.abstractmethod
    def calculate_add(self, __arg1: Any, __arg2: Any) -> Any:
        ...

    @abc.abstractmethod
    def calculate_divide(self, __arg1: Any, __arg2: Any) -> Any:
        ...

    @abc.abstractmethod
    def get_population(self, __arg1: Optional[Any]) -> Any:
        ...


class TaxBenefitSystem(Protocol):
    person_entity: Any

    @abc.abstractmethod
    def get_variable(self, __arg1: Any, __arg2: Any = ...) -> Optional[Any]:
        ...


class Variable(Protocol):
    entity: Any
