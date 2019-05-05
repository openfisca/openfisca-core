import numpy as np

from numpy.testing import assert_array_equal

from openfisca_core.tools import combine


def test_combine():
    condition = np.asarray([True, False, True, True, False])
    value_for_true = np.asarray([1, 2, 3])
    value_for_false = np.asarray([10, 20])

    assert_array_equal(
        combine(condition, value_for_true, value_for_false),
        [1, 10, 2, 3, 20]
    )
