from typing_extensions import TypedDict

import numpy


class MemoryUsage(TypedDict, total = False):
    cell_size: int
    dtype: numpy.dtype
    nb_arrays: int
    nb_cells_by_array: int
    nb_requests: int
    nb_requests_by_array: int
    total_nb_bytes: int
