# -*- coding: utf-8 -*-

import os
from enum import Enum


def assert_near(value, target_value, absolute_error_margin = None, message = '', relative_error_margin = None):
    '''

      :param value: Value returned by the test
      :param target_value: Value that the test should return to pass
      :param absolute_error_margin: Absolute error margin authorized
      :param message: Error message to be displayed if the test fails
      :param relative_error_margin: Relative error margin authorized

      Limit : This function cannot be used to assert near dates or periods.

    '''

    import numpy as np

    if absolute_error_margin is None and relative_error_margin is None:
        absolute_error_margin = 0
    if isinstance(value, (list, tuple)):
        value = np.array(value)
    if isinstance(target_value, (list, tuple)):
        target_value = np.array(target_value)
    if isinstance(message, unicode):
        message = message.encode('utf-8')
    if isinstance(value, np.ndarray):
        if isinstance(target_value, Enum) or (isinstance(target_value, np.ndarray) and target_value.dtype == object):
            if not value.dtype == object:
                assert False("Expected an Enum, got {} of dtype {}".format(value, value.dtype))
            else:
                assert (target_value == value).all(), "Expected {}, got {}".format(target_value, value)
        else:

            if absolute_error_margin is not None:
                assert (abs(target_value - value) <= absolute_error_margin).all(), \
                    '{}{} differs from {} with an absolute margin {} > {}'.format(message, value, target_value,
                        abs(target_value - value), absolute_error_margin)
            if relative_error_margin is not None:
                assert (abs(target_value - value) <= abs(relative_error_margin * target_value)).all(), \
                    '{}{} differs from {} with a relative margin {} > {}'.format(message, value, target_value,
                        abs(target_value - value), abs(relative_error_margin * target_value))
    else:
        if absolute_error_margin is not None:
            assert abs(target_value - value) <= absolute_error_margin, \
                '{}{} differs from {} with an absolute margin {} > {}'.format(message, value, target_value,
                    abs(target_value - value), absolute_error_margin)
        if relative_error_margin is not None:
            assert abs(target_value - value) <= abs(relative_error_margin * target_value), \
                '{}{} differs from {} with a relative margin {} > {}'.format(message, value, target_value,
                    abs(target_value - value), abs(relative_error_margin * target_value))


def indent(text):
    return "  {}".format(text.replace(os.linesep, "{}  ".format(os.linesep)))


def get_trace_tool_link(scenario, variables, api_url, trace_tool_url):
    import json
    import urllib

    scenario_json = scenario.to_json()
    simulation_json = {
        'scenarios': [scenario_json],
        'variables': variables,
        }
    url = trace_tool_url + '?' + urllib.urlencode({
        'simulation': json.dumps(simulation_json),
        'api_url': api_url,
        })
    return url
