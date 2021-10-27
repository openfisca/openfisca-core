from __future__ import annotations

from typing import Any, Dict, Optional

import json
import os
from urllib import parse

import numexpr

from openfisca_core.taxbenefitsystems import TaxBenefitSystem

_tax_benefit_system_cache: Dict[int, TaxBenefitSystem] = {}


def indent(text: str) -> str:
    return "  {}".format(text.replace(os.linesep, "{}  ".format(os.linesep)))


def eval_expression(expression: str) -> Any:
    try:
        return numexpr.evaluate(expression)
    except (KeyError, TypeError):
        return expression


def get_trace_tool_link(
        scenario: Any,
        variables: Any,
        api_url: str,
        trace_tool_url: str,
        ) -> str:

    scenario_json = scenario.to_json()
    simulation_json = {
        'scenarios': [scenario_json],
        'variables': variables,
        }
    url = trace_tool_url + '?' + parse.urlencode({
        'simulation': json.dumps(simulation_json),
        'api_url': api_url,
        })

    return url


def _get_tax_benefit_system(
        baseline: TaxBenefitSystem,
        reforms: object,
        extensions: object,
        ) -> Optional[TaxBenefitSystem]:

    if not isinstance(reforms, list):
        reforms = [reforms]
    if not isinstance(extensions, list):
        extensions = [extensions]

    # keep reforms order in cache, ignore extensions order
    key = hash((id(baseline), ':'.join(reforms), frozenset(extensions)))
    if _tax_benefit_system_cache.get(key):
        return _tax_benefit_system_cache.get(key)

    current_tax_benefit_system = baseline

    for reform_path in reforms:
        current_tax_benefit_system = current_tax_benefit_system.apply_reform(reform_path)

    for extension in extensions:
        current_tax_benefit_system = current_tax_benefit_system.clone()
        current_tax_benefit_system.load_extension(extension)

    _tax_benefit_system_cache[key] = current_tax_benefit_system

    return current_tax_benefit_system
