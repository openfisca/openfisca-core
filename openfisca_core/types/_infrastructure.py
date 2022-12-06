"""Infrastructure-model.

The infrastructure-model is composed of structures meant to encapsulate the
relationships with layers outside of the domain (memory, disk, etc.).

"""

from __future__ import annotations

from typing import Any, Optional
from typing_extensions import Protocol

import abc

import numpy


class Storage(Protocol):
    """Vector storage protocol."""

    @abc.abstractmethod
    def get(self, period: Any) -> Optional[numpy.ndarray]:
        """Abstract method."""

    @abc.abstractmethod
    def put(self, values: Any, period: Any) -> None:
        """Abstract method."""

    @abc.abstractmethod
    def delete(self, period: Any = None) -> None:
        """Abstract method."""

    def get_known_periods(self) -> Any:
        """Storage's known periods."""

    @abc.abstractmethod
    def get_memory_usage(self) -> Any:
        """Memory usage of the storage."""
