# -*- coding: utf-8 -*-


import os

import numexpr

from policyengine_core.enums import EnumArray


def assert_near(
    value,
    target_value,
    absolute_error_margin=None,
    message="",
    relative_error_margin=None,
):
    """

    :param value: Value returned by the test
    :param target_value: Value that the test should return to pass
    :param absolute_error_margin: Absolute error margin authorized
    :param message: Error message to be displayed if the test fails
    :param relative_error_margin: Relative error margin authorized

    Limit : This function cannot be used to assert near periods.

    """

    import numpy as np

    if absolute_error_margin is None and relative_error_margin is None:
        absolute_error_margin = 0
    if not isinstance(value, np.ndarray):
        value = np.array(value)
    if isinstance(value, EnumArray):
        return assert_enum_equals(value, target_value, message)
    if np.issubdtype(value.dtype, np.datetime64):
        target_value = np.array(target_value, dtype=value.dtype)
        assert_datetime_equals(value, target_value, message)
    if isinstance(target_value, str):
        target_value = eval_expression(target_value)

    target_value = np.array(target_value).astype(np.float32)

    value = np.array(value).astype(np.float32)
    diff = abs(target_value - value)
    if absolute_error_margin is not None:
        assert (
            diff <= absolute_error_margin
        ).all(), "{}{} differs from {} with an absolute margin {} > {}".format(
            message, value, target_value, diff, absolute_error_margin
        )
    if relative_error_margin is not None:
        assert (
            diff <= abs(relative_error_margin * target_value)
        ).all(), "{}{} differs from {} with a relative margin {} > {}".format(
            message,
            value,
            target_value,
            diff,
            abs(relative_error_margin * target_value),
        )


def assert_datetime_equals(value, target_value, message=""):
    assert (value == target_value).all(), "{}{} differs from {}.".format(
        message, value, target_value
    )


def assert_enum_equals(value, target_value, message=""):
    value = value.decode_to_str()
    assert (value == target_value).all(), "{}{} differs from {}.".format(
        message, value, target_value
    )


def indent(text):
    return "  {}".format(text.replace(os.linesep, "{}  ".format(os.linesep)))


def get_trace_tool_link(scenario, variables, api_url, trace_tool_url):
    import json
    import urllib

    scenario_json = scenario.to_json()
    simulation_json = {
        "scenarios": [scenario_json],
        "variables": variables,
    }
    url = (
        trace_tool_url
        + "?"
        + urllib.urlencode(
            {
                "simulation": json.dumps(simulation_json),
                "api_url": api_url,
            }
        )
    )
    return url


def eval_expression(expression):
    try:
        return numexpr.evaluate(expression)
    except (KeyError, TypeError):
        return expression
