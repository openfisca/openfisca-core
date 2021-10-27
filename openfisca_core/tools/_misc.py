from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, cast
from openfisca_core.types import TaxBenefitSystemType

import json
import os
from urllib import parse

import numexpr

_tax_benefit_system_cache: Dict[int, TaxBenefitSystemType] = {}


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
        baseline: TaxBenefitSystemType,
        reforms: Sequence[str],
        extensions: Sequence[str],
        ) -> Optional[TaxBenefitSystemType]:

    if not isinstance(reforms, list):
        reforms = cast(Sequence[str], [reforms])
    if not isinstance(extensions, list):
        extensions = cast(Sequence[str], [extensions])

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
