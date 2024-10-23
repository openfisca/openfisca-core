"""Different storage backends for the data of a simulation."""

from .in_memory_storage import InMemoryStorage
from .on_disk_storage import OnDiskStorage

__all__ = ["InMemoryStorage", "OnDiskStorage"]
