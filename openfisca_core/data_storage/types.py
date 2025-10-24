from typing_extensions import TypedDict

from openfisca_core.types import Array, DTypeGeneric, Enum, Period


class MemoryUsage(TypedDict, total=True):
    """Memory usage information."""

    cell_size: float
    nb_arrays: int
    total_nb_bytes: int


__all__ = ["Array", "DTypeGeneric", "Enum", "Period"]
