from typing import Protocol


class HasIndex(Protocol):
    """Indexable class protocol."""

    index: int
