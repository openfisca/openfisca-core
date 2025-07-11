import abc

from openfisca_core import periods


class AtInstantLike(abc.ABC):
    """Base class for various types of parameters implementing the at instant protocol."""

    def __call__(self, instant):
        return self.get_at_instant(instant)

    def get_at_instant(self, instant):
        instant = str(periods.instant(instant))
        return self._get_at_instant(instant)

    @abc.abstractmethod
    def _get_at_instant(self, instant): ...
