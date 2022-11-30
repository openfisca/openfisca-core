from __future__ import annotations

from typing import Any, Optional, Sequence

import numpy

from openfisca_core import periods, types

from ._arrays import Arrays


class InMemoryStorage:
    """
    Low-level class responsible for storing and retrieving calculated vectors in memory
    """

    _arrays: Arrays

    def __init__(self, is_eternal: bool = False) -> None:
        self._arrays = Arrays({})
        self.is_eternal = is_eternal

    def get(self, period: types.Period) -> Any:
        if self.is_eternal:
            period = periods.period(periods.ETERNITY)
        period = periods.period(period)

        values = self._arrays.get(period)
        if values is None:
            return None

        return values

    def put(self, value: Any, period: types.Period) -> None:
        if self.is_eternal:
            period = periods.period(periods.ETERNITY)

        else:
            period = periods.period(period)

        self._arrays = Arrays({period: value, **self._arrays})

    def delete(self, period: Optional[types.Period] = None) -> None:
        if period is None:
            self._arrays = Arrays({})
            return None

        if self.is_eternal:
            period = periods.period(periods.ETERNITY)

        else:
            period = periods.period(period)

        self._arrays = Arrays({
            period_item: value
            for period_item, value in self._arrays.items()
            if not period.contains(period_item)
            })

    def get_known_periods(self) -> Sequence[types.Period]:
        return list(self._arrays.keys())

    def get_memory_usage(self) -> types.MemoryUsage:
        if not self._arrays:
            return types.MemoryUsage(
                cell_size = numpy.nan,
                nb_arrays = 0,
                total_nb_bytes = 0,
                )

        nb_arrays = len(self._arrays)
        array = next(iter(self._arrays.values()))
        total = array.nbytes * nb_arrays

        return types.MemoryUsage(
            cell_size = array.itemsize,
            nb_arrays = nb_arrays,
            total_nb_bytes = total,
            )
