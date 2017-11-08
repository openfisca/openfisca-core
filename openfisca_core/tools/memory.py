# -*- coding: utf-8 -*-

"""
A module to investigate openfisca memory usage
"""

import numpy as np


def get_memory_usage(simulation, variables = None):
    infos_by_variable = dict()
    for column_name, holder in simulation.holder_by_name.iteritems():
        if variables is not None:
            if column_name not in variables:
                continue

        if holder is not None:
            if holder._array is not None:
                # Only used when column.is_permanent
                array = holder._array
                infos_by_variable[column_name] = dict(
                    periods = ['permanent'],
                    ncells = np.prod(array.shape),
                    item_size = array.itemsize,
                    dtype = array.dtype,
                    nbytes = array.nbytes,
                    )
            elif holder._array_by_period is not None:
                periods = sorted(holder._array_by_period.keys())
                array = holder._array_by_period[periods[0]]
                infos_by_variable[column_name] = dict(
                    periods = periods,
                    ncells = np.prod(array.shape),  # per period
                    item_size = array.itemsize,
                    dtype = array.dtype,
                    nbytes = array.nbytes * len(periods),
                    hits = (
                        sum(hits[0] for hits in holder._hits_by_period.values()),
                        sum(hits[1] for hits in holder._hits_by_period.values()),
                        ) if holder._hits_by_period is not None else (None, None),
                    )
    return infos_by_variable
