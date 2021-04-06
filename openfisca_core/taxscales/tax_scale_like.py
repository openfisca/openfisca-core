from __future__ import annotations

import abc
import copy
import typing

import numpy

from openfisca_core import commons


class TaxScaleLike(abc.ABC):
    """
    Base class for various types of tax scales: amount-based tax scales, rate-based
    tax scales...
    """

    name: str
    option: None
    unit: None
    thresholds: typing.List

    @abc.abstractmethod
    def __init__(self, name: typing.Optional[str] = None, option = None, unit = None) -> None:
        self.name = name or "Untitled TaxScale"
        self.option = option
        self.unit = unit
        self.thresholds = []

    def __eq__(self, _other: object) -> typing.NoReturn:
        raise NotImplementedError(
            "Method '__eq__' is not implemented for "
            f"{self.__class__.__name__}",
            )

    def __ne__(self, _other: object) -> typing.NoReturn:
        raise NotImplementedError(
            "Method '__ne__' is not implemented for "
            f"{self.__class__.__name__}",
            )

    @abc.abstractmethod
    def __repr__(self) -> str:
        ...

    @abc.abstractmethod
    def calc(
            self,
            tax_base: typing.Union[numpy.ndarray[int], numpy.ndarray[float]],
            right: bool,
            ) -> numpy.ndarray[float]:
        ...

    @abc.abstractmethod
    def to_dict(self) -> dict:
        ...

    def copy(self) -> typing.Any:
        new = commons.empty_clone(self)
        new.__dict__ = copy.deepcopy(self.__dict__)
        return new
