from __future__ import annotations

import os

import numexpr

from openfisca_core import types as t


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


def eval_expression(
    expression: str,
) -> str | t.Array[t.ArrayBool | t.ArrayInt | t.ArrayFloat]:
    try:
        return numexpr.evaluate(expression)
    except (KeyError, TypeError):
        return expression
