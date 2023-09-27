from abc import abstractmethod
from typing import Protocol


class HasKey(Protocol):
    """Protocol of objects having a key.

    .. versionadded:: 41.0.1

    """

    @property
    @abstractmethod
    def key(self) -> str:
        """A key to identify something."""
