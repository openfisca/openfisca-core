"""Experimental features of OpenFisca-Core."""

from ._errors import MemoryConfigWarning
from ._memory_config import MemoryConfig

__all__ = [
    "MemoryConfig",
    "MemoryConfigWarning",
]
