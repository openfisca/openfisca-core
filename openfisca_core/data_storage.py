# -*- coding: utf-8 -*-

import shutil
import os
from typing import Dict, Optional

import numpy as np

from openfisca_core import periods
from openfisca_core.periods import Period, ETERNITY_PERIOD
from openfisca_core.indexed_enums import EnumArray
from openfisca_core.commons import PartialArray

class InMemoryStorage(object):
    """
    Low-level class responsible for storing and retrieving calculated vectors in memory
    """

    def __init__(self, is_eternal:bool = False):
        self._arrays: Dict = {}
        self.is_eternal = is_eternal

    def get(self, period: Optional[Period]) -> Optional[PartialArray]:
        if self.is_eternal:
            period = ETERNITY_PERIOD

        values = self._arrays.get(period)
        if values is None:
            return None
        return values

    def put(self, value: PartialArray, period: Optional[Period]):
        if self.is_eternal:
            period = ETERNITY_PERIOD

        self._arrays[period] = value

    def delete(self, period: Period = None):
        if period is None or self.is_eternal:
            self._arrays = {}
            return

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

        values = [partial_array.value for partial_array in self._arrays.values()]
        return dict(
            nb_arrays = len(self._arrays),
            total_nb_bytes = sum(value.nbytes for value in values),
            cell_size = values[0].itemsize,
            )


class OnDiskStorage(object):
    """
    Low-level class responsible for storing and retrieving calculated vectors on disk
    """

    def __init__(self, storage_dir: str, is_eternal: bool = False, preserve_storage_dir: bool = False):
        self._files: Dict = {}
        self._enums: Dict = {}
        self.is_eternal = is_eternal
        self.preserve_storage_dir = preserve_storage_dir
        self.storage_dir = storage_dir
        self.values_dir = os.path.join(storage_dir, 'values')
        self.masks_dir = os.path.join(storage_dir, 'masks')
        if not os.path.isdir(self.storage_dir):
            os.mkdir(self.storage_dir)
        if not os.path.isdir(self.values_dir):
            os.mkdir(self.values_dir)
        if not os.path.isdir(self.masks_dir):
            os.mkdir(self.masks_dir)

    def _decode_file(self, file):
        enum = self._enums.get(file)
        if enum is not None:
            return EnumArray(np.load(file), enum)
        else:
            return np.load(file)

    def get(self, period: Optional[Period]) -> Optional[PartialArray]:
        if self.is_eternal:
            period = ETERNITY_PERIOD

        values = self._files.get(period)
        if values is None:
            return None
        values_file, mask_file = values
        values = self._decode_file(values_file)
        mask = self._decode_file(mask_file) if mask_file else None

        return PartialArray(values, mask)

    def put(self, partial_array: PartialArray, period: Optional[Period]):
        if self.is_eternal:
            period = ETERNITY_PERIOD

        value = partial_array.value
        mask = partial_array.mask

        filename = str(period)
        value_file = os.path.join(self.values_dir, filename) + '.npy'
        mask_file =  os.path.join(self.masks_dir, filename) + '.npy'

        if isinstance(value, EnumArray):
            self._enums[value_file] = value.possible_values
            value = value.view(np.ndarray)

        np.save(value_file, value)
        if mask is not None:
            np.save(mask_file, mask)
            self._files[period] = (value_file, mask_file)
        else:
            self._files[period] = (value_file, None)

    def delete(self, period: Optional[Period] = None):
        if period is None or self.is_eternal:
            self._files = {}
            return

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
        for filename in os.listdir(self.values_dir):
            if not filename.endswith('.npy'):
                continue
            values_file = os.path.join(self.values_dir, filename)
            masks_file = os.path.join(self.masks_dir, filename)
            if not os.path.isfile(masks_file):
                masks_file = None
            filename_core = filename.rsplit('.', 1)[0]
            period = periods.period(filename_core)
            files[period] = (values_file, masks_file)

    def __del__(self):
        if self.preserve_storage_dir:
            return
        shutil.rmtree(self.storage_dir)  # Remove the holder temporary files
        # If the simulation temporary directory is empty, remove it
        parent_dir = os.path.abspath(os.path.join(self.storage_dir, os.pardir))
        if not os.listdir(parent_dir):
            shutil.rmtree(parent_dir)
