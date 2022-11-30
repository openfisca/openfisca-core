from __future__ import annotations

from typing import Any, Optional
from typing_extensions import Protocol

import abc

import numpy


class Storage(Protocol):
    """Storage protocol."""

    @abc.abstractmethod
    def get(self, period: Any) -> Optional[numpy.ndarray]:
        """Abstract method."""

    @abc.abstractmethod
    def put(self, values: Any, period: Any) -> None:
        """Abstract method."""

    @abc.abstractmethod
    def delete(self, period: Any = None) -> None:
        """Abstract method."""
