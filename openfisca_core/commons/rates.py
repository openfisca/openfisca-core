from typing import Optional, Sequence

import numpy


def average_rate(
        target: numpy.ndarray,
        varying: Sequence[float],
        trim: Optional[Sequence[float]] = None,
        ) -> numpy.ndarray:
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

    rate: numpy.ndarray
    rate = 1 - target / varying

    if trim is not None:

        rate = numpy.where(
            rate <= max(trim),
            rate,
            numpy.nan,
            )

        rate = numpy.where(
            rate >= min(trim),
            rate,
            numpy.nan,
            )

    return rate


def marginal_rate(
        target: numpy.ndarray,
        varying: numpy.ndarray,
        trim: Optional[numpy.ndarray] = None,
        ) -> numpy.ndarray:
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

    rate: numpy.ndarray

    rate = (
        + 1
        - (target[:-1] - target[1:])
        / (varying[:-1] - varying[1:])
        )

    if trim is not None:

        rate = numpy.where(
            rate <= max(trim),
            rate,
            numpy.nan,
            )

        rate = numpy.where(
            rate >= min(trim),
            rate,
            numpy.nan,
            )

    return rate
