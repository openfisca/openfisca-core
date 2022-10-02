from typing import Optional

import numpy

from policyengine_core.types import ArrayLike, ArrayType


def average_rate(
    target: ArrayType[float],
    varying: ArrayLike[float],
    trim: Optional[ArrayLike[float]] = None,
) -> ArrayType[float]:
    """Computes the average rate of a target net income.

    Given a ``target`` net income, and according to the ``varying`` gross
    income. Optionally, a ``trim`` can be applied consisting of the lower and
    upper bounds of the average rate to be computed.

    Note:
        Usually, ``target`` and ``varying`` are the same size.

    Args:
        target: The targeted net income.
        varying: The varying gross income.
        trim: The lower and upper bounds of the average rate.

    Returns:
        :obj:`numpy.ndarray` of :obj:`float`:

        The average rate for each target.

        When ``trim`` is provided, values that are out of the provided bounds
        are replaced by :obj:`numpy.nan`.

    Examples:
        >>> target = numpy.array([1, 2, 3])
        >>> varying = [2, 2, 2]
        >>> trim = [-1, .25]
        >>> average_rate(target, varying, trim)
        array([ nan,  0. , -0.5])

    """

    average_rate: ArrayType[float]

    average_rate = 1 - target / varying

    if trim is not None:

        average_rate = numpy.where(
            average_rate <= max(trim),
            average_rate,
            numpy.nan,
        )

        average_rate = numpy.where(
            average_rate >= min(trim),
            average_rate,
            numpy.nan,
        )

    return average_rate


def marginal_rate(
    target: ArrayType[float],
    varying: ArrayType[float],
    trim: Optional[ArrayLike[float]] = None,
) -> ArrayType[float]:
    """Computes the marginal rate of a target net income.

    Given a ``target`` net income, and according to the ``varying`` gross
    income. Optionally, a ``trim`` can be applied consisting of the lower and
    upper bounds of the marginal rate to be computed.

    Note:
        Usually, ``target`` and ``varying`` are the same size.

    Args:
        target: The targeted net income.
        varying: The varying gross income.
        trim: The lower and upper bounds of the marginal rate.

    Returns:
        :obj:`numpy.ndarray` of :obj:`float`:

        The marginal rate for each target.

        When ``trim`` is provided, values that are out of the provided bounds
        are replaced by :obj:`numpy.nan`.

    Examples:
        >>> target = numpy.array([1, 2, 3])
        >>> varying = numpy.array([1, 2, 4])
        >>> trim = [.25, .75]
        >>> marginal_rate(target, varying, trim)
        array([nan, 0.5])

    """

    marginal_rate: ArrayType[float]

    marginal_rate = +1 - (target[:-1] - target[1:]) / (
        varying[:-1] - varying[1:]
    )

    if trim is not None:

        marginal_rate = numpy.where(
            marginal_rate <= max(trim),
            marginal_rate,
            numpy.nan,
        )

        marginal_rate = numpy.where(
            marginal_rate >= min(trim),
            marginal_rate,
            numpy.nan,
        )

    return marginal_rate
