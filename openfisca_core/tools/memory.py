# -*- coding: utf-8 -*-

"""
A module to investigate openfisca memory usage
"""

import numpy as np


def memory_usage(simulation):
    infos_by_variable = dict()
    for column_name, holder in simulation.holder_by_name:
        infos = infos_by_variable[column_name] = dict()
        if holder is not None:
            if holder._array is not None:
                # Only used when column.is_permanent
                array = holder._array
                infos.update(
                    periods = ['permanent'],
                    ncells = np.prod(array.shape),
                    item_size = array.itemsize,
                    dtype = array.dtype,
                    nbytes = array.nbytes,
                    )
            elif holder._array_by_period is not None:
                periods = sorted(holder._array_by_period.keys())
                array = holder._array_by_period[periods[0]]
                infos.update(
                    periods = periods,
                    ncells = np.prod(array.shape),  # per period
                    item_size = array.itemsize,
                    dtype = array.dtype,
                    nbytes = array.nbytes * len(periods),
                    )
        return infos_by_variable


def print_memory_usage(simulation):
    infos_by_variable = memory_usage(simulation)
    infos_lines = list()
    for variable, infos in infos_by_variable.iteritems():
        infos_lines.append((infos['nbytes'], variable, "{}: {} cells * item size {} ({}) = {}".format(
            variable,
            infos['ncells'],
            infos['item_size'],
            infos['dtype'],
            infos['nbytes'],
            )))
    infos.sort()
    for _, _, line in infos:
        print(line.rjust(100))


def print_memory_usage_old(simulation):
    infos = []
    for column_name in simulation.tax_benefit_system.column_by_name.iterkeys():
        holder = simulation.holder_by_name.get(column_name)
        if holder is not None:
            if holder._array is not None:
                # Only used when column.is_permanent
                array = holder._array
                infos.append((array.nbytes, column_name, "{}: {} cells * item size {} ({}) = {}".format(
                    column_name,
                    np.prod(array.shape),
                    array.itemsize,
                    array.dtype,
                    array.nbytes,
                    )))
            elif holder._array_by_period is not None:
                periods = sorted(holder._array_by_period.keys())
                array = holder._array_by_period[periods[0]]
                infos.append((len(periods) * array.nbytes, column_name, "{}: {} periods * {} cells * item size {} ({}) = {}".format(
                    column_name,
                    len(periods),
                    np.prod(array.shape),
                    array.itemsize,
                    array.dtype,
                    len(periods) * array.nbytes,
                    )))
    infos.sort()
    for _, _, line in infos:
        print(line.rjust(100))
