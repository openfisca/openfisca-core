from typing import Any, NoReturn, Optional
from typing_extensions import Protocol

import abc


class Entity(Protocol):
    key: str

    @abc.abstractmethod
    def check_role_validity(self, role: Any) -> Optional[NoReturn]:
        ...

    @abc.abstractmethod
    def check_variable_defined_for_entity(
            self,
            variable_name: str,
            ) -> Optional[NoReturn]:
        ...


class Period(Protocol):
    ...


class Population(Protocol):
    ...


class Role(Protocol):
    ...


class Simulation(Protocol):
    ...


class TaxBenefitSystem(Protocol):
    ...
