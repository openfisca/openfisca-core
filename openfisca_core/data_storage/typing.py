"""Infrastructure-model.

The infrastructure-model is composed of structures meant to encapsulate the
relationships with layers outside of the domain (memory, disk, etc.).

"""

from __future__ import annotations

from typing import Any
from typing_extensions import Protocol

import abc


class Storage(Protocol):
    @abc.abstractmethod
    def get(self, period: Any) -> Any: ...

    @abc.abstractmethod
    def put(self, values: Any, period: Any) -> None: ...

    @abc.abstractmethod
    def delete(self, period: Any = None) -> None: ...

    def periods(self) -> Any: ...

    @abc.abstractmethod
    def usage(self) -> Any: ...
