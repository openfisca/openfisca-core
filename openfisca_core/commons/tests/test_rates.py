import math

import numpy
from numpy.testing import assert_array_equal

from openfisca_core import commons


def test_average_rate_when_varying_is_zero() -> None:
    """Yield infinity when the varying gross income crosses zero."""

    target = numpy.array([1, 2, 3])
    varying = [0, 0, 0]

    result = commons.average_rate(target, varying)

    assert_array_equal(result, numpy.array([-math.inf, -math.inf, -math.inf]))


def test_marginal_rate_when_varying_is_zero() -> None:
    """Yield infinity when the varying gross income crosses zero."""

    target = numpy.array([1, 2, 3])
    varying = numpy.array([0, 0, 0])

    result = commons.marginal_rate(target, varying)

    assert_array_equal(result, numpy.array([math.inf, math.inf]))
