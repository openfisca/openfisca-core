from __future__ import annotations

from typing import Any, Optional
from openfisca_core.typing import ArrayType, ArrayLike

import datetime

import numpy

from openfisca_core.indexed_enums import EnumArray

from . import _misc


def assert_near(
        value: ArrayType,
        target_value: Any,
        absolute_error_margin: Optional[float] = None,
        message: str = '',
        relative_error_margin: Optional[float] = None,
        ) -> None:
    '''

      :param value: Value returned by the test
      :param target_value: Value that the test should return to pass
      :param absolute_error_margin: Absolute error margin authorized
      :param message: Error message to be displayed if the test fails
      :param relative_error_margin: Relative error margin authorized

      Limit : This function cannot be used to assert near periods.

    '''

    if absolute_error_margin is None and relative_error_margin is None:
        absolute_error_margin = 0
    if not isinstance(value, numpy.ndarray):
        value = numpy.array(value)
    if isinstance(value, EnumArray):
        return assert_enum_equals(value, target_value, message)
    if numpy.issubdtype(value.dtype, numpy.datetime64):
        target_value = numpy.array(target_value, dtype = value.dtype)
        assert_datetime_equals(value, target_value, message)
    if isinstance(target_value, str):
        target_value = _misc.eval_expression(target_value)

    target_value = numpy.array(target_value).astype(numpy.float32)

    value = numpy.array(value).astype(numpy.float32)
    diff = abs(target_value - value)
    if absolute_error_margin is not None:
        assert (diff <= absolute_error_margin).all(), \
            '{}{} differs from {} with an absolute margin {} > {}'.format(message, value, target_value,
                diff, absolute_error_margin)
    if relative_error_margin is not None:
        assert (diff <= abs(relative_error_margin * target_value)).all(), \
            '{}{} differs from {} with a relative margin {} > {}'.format(message, value, target_value,
                diff, abs(relative_error_margin * target_value))


def assert_datetime_equals(
        value: ArrayType[datetime.date],
        target_value: ArrayLike[datetime.date],
        message: str = '',
        ) -> None:

    assert (value == target_value).all(), '{}{} differs from {}.'.format(message, value, target_value)


def assert_enum_equals(
        value: EnumArray,
        target_value: str,
        message: str = '',
        ) -> None:

    value_ = value.decode_to_str()

    assert (value_ == target_value).all(), '{}{} differs from {}.'.format(message, value, target_value)
