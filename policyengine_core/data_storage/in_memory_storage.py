from typing import Dict, Union
import numpy
from numpy.typing import ArrayLike
from policyengine_core import periods
from policyengine_core.periods import Period


class InMemoryStorage:
    """
    Low-level class responsible for storing and retrieving calculated vectors in memory
    """

    _arrays: Dict[Period, ArrayLike]
    is_eternal: bool

    def __init__(self, is_eternal: bool):
        self._arrays = {}
        self.is_eternal = is_eternal

    def get(self, period: Period) -> ArrayLike:
        if self.is_eternal:
            period = periods.period(periods.ETERNITY)
        period = periods.period(period)

        values = self._arrays.get(period)
        if values is None:
            return None
        return values

    def put(self, value: ArrayLike, period: Period) -> None:
        if self.is_eternal:
            period = periods.period(periods.ETERNITY)
        period = periods.period(period)

        self._arrays[period] = value

    def delete(self, period: Period = None) -> None:
        if period is None:
            self._arrays = {}
            return

        if self.is_eternal:
            period = periods.period(periods.ETERNITY)
        period = periods.period(period)

        self._arrays = {
            period_item: value
            for period_item, value in self._arrays.items()
            if not period.contains(period_item)
        }

    def get_known_periods(self) -> list:
        return list(self._arrays.keys())

    def get_memory_usage(self) -> dict:
        if not self._arrays:
            return dict(
                nb_arrays=0,
                total_nb_bytes=0,
                cell_size=numpy.nan,
            )

        nb_arrays = len(self._arrays)
        array = next(iter(self._arrays.values()))
        return dict(
            nb_arrays=nb_arrays,
            total_nb_bytes=array.nbytes * nb_arrays,
            cell_size=array.itemsize,
        )
