# -*- coding: utf-8 -*-

import shutil
import os

import numpy as np

from openfisca_core import periods
from openfisca_core.periods import ETERNITY
from openfisca_core.indexed_enums import EnumArray


class InMemoryStorage(object):
    """
    Low-level class responsible for storing and retrieving calculated vectors in memory
    """

    def __init__(self, is_eternal = False):
        self._arrays = {}
        self.is_eternal = is_eternal

    def get(self, period):
        if self.is_eternal:
            period = periods.period(ETERNITY)
        period = periods.period(period)

        values = self._arrays.get(period)
        if values is None:
            return None
        if isinstance(values, dict):
            return next(iter(values.values()))
        return values

    def put(self, value, period):
        if self.is_eternal:
            period = periods.period(ETERNITY)
        period = periods.period(period)

        self._arrays[period] = value

    def delete(self, period = None):
        if period is None:
            self._arrays = {}
            return

        if self.is_eternal:
            period = periods.period(ETERNITY)
        period = periods.period(period)

        self._arrays = {
            period_item: value
            for period_item, value in self._arrays.items()
            if not period.contains(period_item)
            }

    def get_known_periods(self):
        return self._arrays.keys()

    def get_memory_usage(self):
        if not self._arrays:
            return dict(
                nb_arrays = 0,
                total_nb_bytes = 0,
                cell_size = np.nan,
                )

        nb_arrays = sum([
            len(array_or_dict) if isinstance(array_or_dict, dict) else 1
            for array_or_dict in self._arrays.values()
            ])

        array = next(iter(self._arrays.values()))
        if isinstance(array, dict):
            array = array.values()[0]
        return dict(
            nb_arrays = nb_arrays,
            total_nb_bytes = array.nbytes * nb_arrays,
            cell_size = array.itemsize,
            )


class OnDiskStorage(object):
    """
    Low-level class responsible for storing and retrieving calculated vectors on disk
    """

    def __init__(self, storage_dir, is_eternal = False, preserve_storage_dir = False):
        self._files = {}
        self._enums = {}
        self.is_eternal = is_eternal
        self.preserve_storage_dir = preserve_storage_dir
        self.storage_dir = storage_dir

    def _decode_file(self, file):
        enum = self._enums.get(file)
        if enum is not None:
            return EnumArray(np.load(file), enum)
        else:
            return np.load(file)

    def get(self, period):
        if self.is_eternal:
            period = periods.period(ETERNITY)
        period = periods.period(period)

        values = self._files.get(period)
        if values is None:
            return None
        if isinstance(values, dict):
            return self._decode_file(next(iter(values.values())))
        return self._decode_file(values)

    def put(self, value, period):
        if self.is_eternal:
            period = periods.period(ETERNITY)
        period = periods.period(period)

        filename = str(period)
        path = os.path.join(self.storage_dir, filename) + '.npy'
        if isinstance(value, EnumArray):
            self._enums[path] = value.possible_values
            value = value.view(np.ndarray)
        np.save(path, value)
        self._files[period] = path

    def delete(self, period = None):
        if period is None:
            self._files = {}
            return

        if self.is_eternal:
            period = periods.period(ETERNITY)
        period = periods.period(period)

        if period is not None:
            self._files = {
                period_item: value
                for period_item, value in self._files.items()
                if not period.contains(period_item)
                }

    def get_known_periods(self):
        return self._files.keys()

    def restore(self):
        self._files = files = {}
        # Restore self._files from content of storage_dir.
        for filename in os.listdir(self.storage_dir):
            if not filename.endswith('.npy'):
                continue
            path = os.path.join(self.storage_dir, filename)
            filename_core = filename.rsplit('.', 1)[0]
            period = periods.period(filename_core)
            files[period] = path

    def __del__(self):
        if self.preserve_storage_dir:
            return
        shutil.rmtree(self.storage_dir)  # Remove the holder temporary files
        # If the simulation temporary directory is empty, remove it
        parent_dir = os.path.abspath(os.path.join(self.storage_dir, os.pardir))
        if not os.listdir(parent_dir):
            shutil.rmtree(parent_dir)
