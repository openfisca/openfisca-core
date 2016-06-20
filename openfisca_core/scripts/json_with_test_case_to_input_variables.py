#! /usr/bin/env python
# -*- coding: utf-8 -*-


"""Convert a scenario or simulation JSON containing a test case to the same JSON with input variables."""


import argparse
import copy
import importlib
import json
import logging
import sys

from biryani.baseconv import check


args = None


def json_with_test_case_to_input_variables(scenario_or_simulation_json):
    country_package = importlib.import_module(args.country_package_name)
    tax_benefit_system = country_package.init_tax_benefit_system()
    new_scenario_or_simulation_json = copy.deepcopy(scenario_or_simulation_json)
    new_scenarios_json = new_scenario_or_simulation_json['scenarios'] \
        if 'scenarios' in new_scenario_or_simulation_json \
        else [new_scenario_or_simulation_json]
    assert all('test_case' in scenario_json for scenario_json in new_scenarios_json), \
        'All the scenarios must have a test case.'
    for new_scenario_json in new_scenarios_json:
        scenario = check(tax_benefit_system.Scenario.make_json_to_instance(
            repair = True,
            tax_benefit_system = tax_benefit_system,
            ))(new_scenario_json)
        scenario.suggest()
        simulation = scenario.new_simulation(use_set_input_hooks = False)
        input_variables_json = simulation.to_input_variables_json()
        del new_scenario_json['test_case']
        new_scenario_json['input_variables'] = input_variables_json
    return new_scenario_or_simulation_json


def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('country_package_name', help = "country package name (ex: openfisca_france)")
    parser.add_argument('-i', '--input-file', type = argparse.FileType('r'), default = '-', help = 'JSON scenario')
    parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = "increase output verbosity")
    global args
    args = parser.parse_args()
    logging.basicConfig(level = logging.DEBUG if args.verbose else logging.WARNING, stream = sys.stdout)
    scenario_or_simulation_str = args.input_file.read()
    scenario_or_simulation_json = json.loads(scenario_or_simulation_str)
    new_scenario_or_simulation_json = json_with_test_case_to_input_variables(scenario_or_simulation_json)
    print json.dumps(new_scenario_or_simulation_json, indent = 2, sort_keys = True).encode('utf-8')


if __name__ == "__main__":
    sys.exit(main())
