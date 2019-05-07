import numpy as np

from numpy.testing import assert_array_equal

from openfisca_core.tools import ternary_combine, combine


def test_ternary_combine():
    condition = np.asarray([True, False, True, True, False])
    value_for_true = np.asarray([1, 2, 3])
    value_for_false = np.asarray([10, 20])

    assert_array_equal(
        ternary_combine(condition, value_for_true, value_for_false),
        [1, 10, 2, 3, 20]
        )


def test_combine():
    condition_1 = np.asarray([True, False, True, True, False])
    condition_2 = np.asarray([True, True, True, False, True])
    value_1 = np.asarray([1, 3, 4])
    value_2 = np.asarray([10, 20, 30, 50])

    assert_array_equal(
        combine([(condition_1, value_1), (condition_2, value_2)]),
        [1, 20, 3, 4, 50]
        )
