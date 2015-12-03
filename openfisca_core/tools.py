# -*- coding: utf-8 -*-


import json
import urllib

import numpy as np


__all__ = [
    'assert_near',
    'empty_clone',
    'stringify_array',
    ]


class Dummy(object):
    """A class that does nothing

    Used by function ``empty_clone`` to create an empty instance from an existing object.
    """
    pass


def assert_near(value, target_value, absolute_error_margin = None, message = '', relative_error_margin = None):
    if absolute_error_margin is None and relative_error_margin is None:
        absolute_error_margin = 0
    if isinstance(value, (list, tuple)):
        value = np.array(value)
    if isinstance(target_value, (list, tuple)):
        target_value = np.array(target_value)
    if isinstance(message, unicode):
        message = message.encode('utf-8')
    if isinstance(value, np.ndarray):
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


def get_trace_tool_link(scenario, variables, api_url, trace_tool_url):
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


def empty_clone(original):
    """Create a new empty instance of the same class of the original object."""
    new = Dummy()
    new.__class__ = original.__class__
    return new


def stringify_array(array):
    """Generate a clean string representation of a NumPY array.

    This function exists, because str(array) sucks for logs, etc.
    """
    return u'[{}]'.format(u', '.join(
        unicode(cell)
        for cell in array
        )) if array is not None else u'None'
