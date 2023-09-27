from abc import abstractmethod
from typing import Protocol


class HasKey(Protocol):
    """Protocol of objects having a key.

    .. versionadded:: 41.0.1

    .. versionchanged:: 41.0.2
        Renamed from ``Entity`` to make it generic.

    """

    @property
    @abstractmethod
    def key(self) -> str:
        """A key to identify something."""
