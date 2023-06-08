from typing_extensions import TypedDict

import numpy


class MemoryUsage(TypedDict, total=False):
    """Virtual memory usage of a Holder.

    Attributes:
        cell_size: The amount of bytes assigned to each value.
        dtype: The :mod:`numpy.dtype` of any, each, and every value.
        nb_arrays: The number of periods for which the Holder contains values.
        nb_cells_by_array: The number of entities in the current Simulation.
        nb_requests: The number of times the Variable has been computed.
        nb_requests_by_array: Average times a stored array has been read.
        total_nb_bytes: The total number of bytes used by the Holder.

    """

    cell_size: int
    dtype: numpy.dtype
    nb_arrays: int
    nb_cells_by_array: int
    nb_requests: int
    nb_requests_by_array: int
    total_nb_bytes: int
