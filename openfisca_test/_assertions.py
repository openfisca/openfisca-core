from __future__ import annotations

import numpy

from ._parsers import parse


def assert_near(
    actual: object,
    expected: object,
    /,
    message: str = "",
    *,
    absolute_error_margin: float = 0,
    relative_error_margin: float = 0,
) -> None:
    """Assert that two values are near each other.

    Args:
        actual: Value returned by the test.
        expected: Value that the test should return to pass.
        message: Error message to be displayed if the test fails.
        absolute_error_margin: Absolute error margin authorized.
        relative_error_margin: Relative error margin authorized.

    Returns:
        None

    Raises:
        ValueError: If the error margin is negative.
        AssertionError: If the two values are not near each other.
        NotImplementedError: If the data type is not supported.

    Note:
        This function cannot be used to assert near periods.

    Examples:
        >>> actual = numpy.array([1.0, 2.0, 3.0])
        >>> expected = numpy.array([1.0, 2.0, 2.9])
        >>> assert_near(actual, expected, absolute_error_margin=0.2)

        >>> expected = numpy.array([1.0, 2.0, 2.95])
        >>> assert_near(actual, expected, absolute_error_margin=0.1)

        >>> assert_near(actual, expected, relative_error_margin=0.05)

        >>> assert_near(True, [True])

    """

    # Validate absolute_error_margin.
    if absolute_error_margin < 0:
        raise ValueError("The absolute error margin must be positive.")

    # Validate relative_error_margin.
    if relative_error_margin < 0:
        raise ValueError("The relative error margin must be positive.")

    # Parse the actual value.
    actual = parse(actual)

    # Parse the expected value.
    expected = parse(expected)

    # Get the common data type.
    try:
        common_dtype = numpy.promote_types(actual.dtype, expected.dtype)

    except TypeError:
        raise AssertionError(
            f"Incompatible types: {actual.dtype} and {expected.dtype}."
        )

    if numpy.issubdtype(common_dtype, numpy.datetime64):
        actual = actual.astype(numpy.datetime64)
        expected = expected.astype(numpy.datetime64)
        assert (actual == expected).all(), f"{message}{actual} differs from {expected}."
        return None

    if numpy.issubdtype(common_dtype, numpy.bool_):
        actual = actual.astype(numpy.bool_)
        expected = expected.astype(numpy.bool_)
        assert (actual == expected).all(), f"{message}{actual} differs from {expected}."
        return None

    if numpy.issubdtype(common_dtype, numpy.bytes_):
        actual = actual.astype(numpy.bytes_)
        expected = expected.astype(numpy.bytes_)
        assert (actual == expected).all(), f"{message}{actual} differs from {expected}."
        return None

    if numpy.issubdtype(common_dtype, numpy.str_):
        actual = actual.astype(numpy.str_)
        expected = expected.astype(numpy.str_)
        assert (actual == expected).all(), f"{message}{actual} differs from {expected}."
        return None

    if numpy.issubdtype(common_dtype, numpy.int32) or numpy.issubdtype(
        common_dtype, numpy.int64
    ):
        actual = actual.astype(numpy.int32)
        expected = expected.astype(numpy.int32)
        diff = abs(expected - actual)
        assert (
            diff == 0
        ).all(), f"{message}{actual} differs from {expected} by {diff}."
        return None

    if numpy.issubdtype(common_dtype, numpy.float32) or numpy.issubdtype(
        common_dtype, numpy.float64
    ):
        actual = actual.astype(numpy.float32)
        expected = expected.astype(numpy.float32)
        diff = abs(expected - actual)
        if absolute_error_margin > 0:
            assert (diff <= absolute_error_margin).all(), (
                f"{message}{actual} differs from {expected} with an absolute margin "
                f"{diff} > {absolute_error_margin}"
            )
            return None
        if relative_error_margin > 0:
            assert (diff <= abs(relative_error_margin * expected)).all(), (
                f"{message}{actual} differs from {expected} with a relative margin "
                f"{diff} > {abs(relative_error_margin * expected)}"
            )
            return None
        assert (
            actual == expected
        ).all(), f"{message}{actual} differs from {expected} by {diff}."
        return None

    raise NotImplementedError


__all__ = ["assert_near"]
