from __future__ import annotations

import typing

import abc
import copy

from openfisca_core import commons

if typing.TYPE_CHECKING:
    import numpy

    NumericalArray = typing.Union[numpy.int32, numpy.float32]


class TaxScaleLike(abc.ABC):
    """Base class for various types of tax scales: amount-based tax scales,
    rate-based tax scales...
    """

    name: str | None
    option: typing.Any
    unit: typing.Any
    thresholds: list

    @abc.abstractmethod
    def __init__(
        self,
        name: str | None = None,
        option: typing.Any = None,
        unit: typing.Any = None,
    ) -> None:
        self.name = name or "Untitled TaxScale"
        self.option = option
        self.unit = unit
        self.thresholds = []

    def __eq__(self, _other: object) -> typing.NoReturn:
        msg = "Method '__eq__' is not implemented for " f"{self.__class__.__name__}"
        raise NotImplementedError(
            msg,
        )

    def __ne__(self, _other: object) -> typing.NoReturn:
        msg = "Method '__ne__' is not implemented for " f"{self.__class__.__name__}"
        raise NotImplementedError(
            msg,
        )

    @abc.abstractmethod
    def __repr__(self) -> str: ...

    @abc.abstractmethod
    def calc(
        self,
        tax_base: NumericalArray,
        right: bool,
    ) -> numpy.float32: ...

    @abc.abstractmethod
    def to_dict(self) -> dict: ...

    def copy(self) -> typing.Any:
        new = commons.empty_clone(self)
        new.__dict__ = copy.deepcopy(self.__dict__)
        return new
