import os

from openfisca_core import commons
from openfisca_core.indexed_enums import EnumArray


def assert_near(
    value,
    target_value,
    absolute_error_margin=None,
    message="",
    relative_error_margin=None,
):
    """:param value: Value returned by the test
    :param target_value: Value that the test should return to pass
    :param absolute_error_margin: Absolute error margin authorized
    :param message: Error message to be displayed if the test fails
    :param relative_error_margin: Relative error margin authorized

    Limit : This function cannot be used to assert near periods.

    """
    import numpy

    if absolute_error_margin is None and relative_error_margin is None:
        absolute_error_margin = 0
    if not isinstance(value, numpy.ndarray):
        value = numpy.array(value)
    if isinstance(value, EnumArray):
        return assert_enum_equals(value, target_value, message)
    if numpy.issubdtype(value.dtype, numpy.datetime64):
        target_value = numpy.array(target_value, dtype=value.dtype)
        assert_datetime_equals(value, target_value, message)
    if isinstance(target_value, str):
        target_value = commons.eval_expression(target_value)

    target_value = numpy.array(target_value).astype(numpy.float32)

    value = numpy.array(value).astype(numpy.float32)
    diff = abs(target_value - value)
    if absolute_error_margin is not None:
        assert (
            diff <= absolute_error_margin
        ).all(), f"{message}{value} differs from {target_value} with an absolute margin {diff} > {absolute_error_margin}"
    if relative_error_margin is not None:
        assert (
            diff <= abs(relative_error_margin * target_value)
        ).all(), f"{message}{value} differs from {target_value} with a relative margin {diff} > {abs(relative_error_margin * target_value)}"
        return None
    return None


def assert_datetime_equals(value, target_value, message="") -> None:
    assert (
        value == target_value
    ).all(), f"{message}{value} differs from {target_value}."


def assert_enum_equals(value, target_value, message="") -> None:
    value = value.decode_to_str()
    assert (
        value == target_value
    ).all(), f"{message}{value} differs from {target_value}."


def indent(text):
    return "  {}".format(text.replace(os.linesep, f"{os.linesep}  "))


def get_trace_tool_link(scenario, variables, api_url, trace_tool_url):
    import json
    import urllib

    scenario_json = scenario.to_json()
    simulation_json = {
        "scenarios": [scenario_json],
        "variables": variables,
    }
    return (
        trace_tool_url
        + "?"
        + urllib.urlencode(
            {
                "simulation": json.dumps(simulation_json),
                "api_url": api_url,
            },
        )
    )
