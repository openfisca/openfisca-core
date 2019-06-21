# -*- coding: utf-8 -*-

from typing import Optional, List, Dict

from openfisca_core.types import Array
from openfisca_core.periods import Period


class Cache:


    def get(self, variable: str, period: Period) -> Optional[Array]:
        """
            Get the cached value of ``variable`` for the given period.

            If the value is not known, return ``None``.
        """
        pass

    def put(self, variable: str, period: Period, value: Array) -> None:
        """
            Store ``value`` in cache for ``variable`` at period ``period``.
        """
        pass

    def delete(self, variable: str, period: Optional[Period] = None) -> None:
        """
            If ``period`` is ``None``, remove all known values of the variable.

            If ``period`` is not ``None``, only remove all values for any period included in period (e.g. if period is "2017", values for "2017-01", "2017-07", etc. would be removed)
        """
        pass

    def get_known_periods(self, variable: str) -> List[Period]:
        """
            Get the list of periods the ``variable`` value is known for.
        """
        pass

    def get_memory_usage(self) -> Dict[str, Dict]:
        """
            Get data about the virtual memory usage of the holder.
        """
        pass
