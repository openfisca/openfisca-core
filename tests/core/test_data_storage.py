# -*- coding: utf-8 -*-

import tempfile

import numpy as np
from numpy.testing import assert_array_equal
from pytest import fixture

from openfisca_core.data_storage import OnDiskStorage
from openfisca_core.commons import PartialArray
from openfisca_core.periods import period as make_period


period = make_period('2019-05')


@fixture
def disk_storage():
    temp_dir = tempfile.mkdtemp(prefix = "openfisca_test_")
    return OnDiskStorage(temp_dir)


def test_put_get(disk_storage):
    array = PartialArray(np.asarray([1,2,3]), np.asarray([True, True, False, True, False]))
    disk_storage.put(array, period)
    cached_array = disk_storage.get(period)
    assert_array_equal(array.value, cached_array.value)
    assert_array_equal(array.mask, cached_array.mask)


def test_put_get_2(disk_storage):
    array = PartialArray(np.asarray([1,2,3]), None)
    disk_storage.put(array, period)
    cached_array = disk_storage.get(period)
    assert_array_equal(array.value, cached_array.value)
    assert array.mask is None
