import abc
from typing import Any

from policyengine_core import periods
from policyengine_core.periods import Instant


class AtInstantLike(abc.ABC):
    """
    Base class for various types of parameters implementing the at instant protocol.
    """

    def __call__(self, instant: Instant) -> Any:
        return self.get_at_instant(instant)

    def get_at_instant(self, instant: Instant) -> Any:
        instant = str(periods.instant(instant))
        return self._get_at_instant(instant)

    @abc.abstractmethod
    def _get_at_instant(self, instant):
        ...
