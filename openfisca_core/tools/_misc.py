from __future__ import annotations

import os

import numexpr


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


def eval_expression(expression):
    try:
        return numexpr.evaluate(expression)
    except (KeyError, TypeError):
        return expression
