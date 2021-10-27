from __future__ import annotations

from typing import Any, Optional
from typing_extensions import Protocol

import abc


class TaxBenefitSystemType(Protocol):
    """Duck-type for tax-benefit systems.
    .. versionadded:: 35.7.0
    """

    @abc.abstractmethod
    def get_variable(self, __arg1: str, __arg2: bool = False) -> Optional[Any]:
        """A tax-benefit system implements :meth:`.get_variable`."""
