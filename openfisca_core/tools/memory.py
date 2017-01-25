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
                    )
    return infos_by_variable


def print_memory_usage(simulation):
    infos_by_variable = get_memory_usage(simulation)
    infos_lines = list()
    for variable, infos in infos_by_variable.iteritems():
        infos_lines.append((infos['nbytes'], variable, "{}: {} periods * {} cells * item size {} ({}) = {}".format(
            variable,
            len(infos['periods']),
            infos['ncells'],
            infos['item_size'],
            infos['dtype'],
            infos['nbytes'],
            )))
    infos_lines.sort()
    for _, _, line in infos_lines:
        print(line.rjust(100))
