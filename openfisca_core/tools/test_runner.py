# -*- coding: utf-8 -*-

"""
A module to run openfisca yaml tests
"""

from __future__ import unicode_literals, print_function, division, absolute_import
from builtins import str

import collections
import copy
import glob
import os
import sys
import unittest
import logging

import nose
import numpy as np
import yaml

from openfisca_core import conv, periods, scenarios
from openfisca_core.tools import assert_near
from openfisca_core.commons import to_unicode


log = logging.getLogger(__name__)

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    log.warning(
        ' '
        'libyaml is not installed in your environment, this can make your '
        'test suite slower to run. Once you have installed libyaml, run `pip '
        'uninstall pyyaml && pip install pyyaml --no-cache-dir` so that it is used in your '
        'Python environment.')
    from yaml import Loader, Dumper


# Yaml module configuration


class unicode_folder(str):
    pass


class unicode_literal(str):
    pass


Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, lambda loader, node: collections.OrderedDict(loader.construct_pairs(node)))
Dumper.add_representer(collections.OrderedDict, lambda dumper, data: dumper.represent_dict((copy.deepcopy(key), value) for key, value in data.items()))
Dumper.add_representer(dict, lambda dumper, data: dumper.represent_dict((copy.deepcopy(key), value) for key, value in data.items()))
Dumper.add_representer(np.ndarray, lambda dumper, data: dumper.represent_list(data.tolist()))
Dumper.add_representer(tuple, lambda dumper, data: dumper.represent_list(data))
Dumper.add_representer(unicode_folder, lambda dumper, data: dumper.represent_scalar('tag:yaml.org,2002:str', data, style='>'))
Dumper.add_representer(unicode_literal, lambda dumper, data: dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|'))
Dumper.add_representer(periods.Instant, lambda dumper, data: dumper.represent_scalar('tag:yaml.org,2002:str', str(data)))
Dumper.add_representer(periods.Period, lambda dumper, data: dumper.represent_scalar('tag:yaml.org,2002:str', str(data)))
Dumper.add_representer(str, lambda dumper, data: dumper.represent_scalar('tag:yaml.org,2002:str', data))


# Exposed methods

def generate_tests(tax_benefit_system, paths, options = {}):
    """
    Generates a lazy iterator of all the YAML tests contained in a file or a directory.

    :parameters: Same as :meth:`run_tests`

    :return: a generator of YAML tests

    """

    if isinstance(paths, str):
        paths = [paths]

    for path in paths:
        if os.path.isdir(path):
            for test in _generate_tests_from_directory(tax_benefit_system, path, options):
                yield test
        else:
            for test in _generate_tests_from_file(tax_benefit_system, path, options):
                yield test


def run_tests(tax_benefit_system, paths, options = {}):
    """
    Runs all the YAML tests contained in a file or a directory.

    If `path` is a directory, subdirectories will be recursively explored.

    :param TaxBenefitSystem tax_benefit_system: the tax-benefit system to use to run the tests
    :param (str/list) paths: A path, or a list of paths, towards the files or directories containing the tests to run. If a path is a directory, subdirectories will be recursively explored.
    :param dict options: See more details below.

    :raises AssertionError: if a test does not pass

    :return: the number of sucessful tests excecuted

    **Testing options**:

    +-------------------------------+-----------+-------------------------------------------+
    | Key                           | Type      | Role                                      |
    +===============================+===========+===========================================+
    | verbose                       | ``bool``  |                                           |
    +-------------------------------+-----------+ See :any:`openfisca-run-test` options doc +
    | name_filter                   | ``str``   |                                           |
    +-------------------------------+-----------+-------------------------------------------+

    """
    argv = sys.argv[:1]  # Nose crashes if it gets any unexpected argument.
    if options.get('verbose'):
        argv.append('--nocapture')  # Do not capture output when verbose mode is activated
    argv.append('--nologcapture')  # Do not capture logs so that the user can define a log level
    return nose.run(
        # The suite argument must be a lambda for nose to run the tests lazily
        suite = lambda: generate_tests(tax_benefit_system, paths, options),
        argv = argv,
        )


# Internal methods

def _generate_tests_from_file(tax_benefit_system, path_to_file, options):
    filename = os.path.splitext(os.path.basename(path_to_file))[0]
    name_filter = options.get('name_filter')
    if isinstance(name_filter, str):
        name_filter = to_unicode(name_filter)
    verbose = options.get('verbose')
    only_variables = options.get('only_variables')
    ignore_variables = options.get('ignore_variables')

    tests = _parse_test_file(tax_benefit_system, path_to_file)

    for test_index, (path_to_file, name, period_str, test) in enumerate(tests, 1):
        if name_filter is not None and name_filter not in filename \
                and name_filter not in (test.get('name', '')) \
                and name_filter not in (test.get('keywords', [])):
            continue

        keywords = test.get('keywords', [])
        title = "{}: {}{} - {}".format(
            os.path.basename(path_to_file),
            '[{}] '.format(', '.join(keywords)) if keywords else '',
            name,
            period_str,
            )

        def check():
            try:
                _run_test(period_str, test, verbose, only_variables, ignore_variables, options)
            except Exception:
                log.error(title)
                raise

        yield unittest.FunctionTestCase(check)


def _generate_tests_from_directory(tax_benefit_system, path_to_dir, options):
    yaml_paths = glob.glob(os.path.join(path_to_dir, "*.yaml"))
    subdirectories = glob.glob(os.path.join(path_to_dir, "*/"))

    for yaml_path in yaml_paths:
        for test in _generate_tests_from_file(tax_benefit_system, yaml_path, options):
            yield test

    for subdirectory in subdirectories:
        for test in _generate_tests_from_directory(tax_benefit_system, subdirectory, options):
            yield test


def _parse_test_file(tax_benefit_system, yaml_path):
    filename = os.path.splitext(os.path.basename(yaml_path))[0]
    with open(yaml_path) as yaml_file:
        try:
            tests = yaml.load(yaml_file, Loader=Loader)
        except yaml.scanner.ScannerError:
            log.error("{} is not a valid YAML file".format(yaml_path).encode('utf-8'))
            raise

    tests, error = conv.pipe(
        conv.make_item_to_singleton(),
        conv.uniform_sequence(
            conv.noop,
            drop_none_items = True,
            ),
        )(tests)

    if error is not None:
        embedding_error = conv.embed_error(tests, 'errors', error)
        assert embedding_error is None, embedding_error
        raise ValueError("Error in test {}:\n{}".format(yaml_path, yaml.dump(tests, Dumper=Dumper, allow_unicode = True,
            default_flow_style = False, indent = 2, width = 120)))

    for test in tests:
        current_tax_benefit_system = tax_benefit_system
        if test.get('reforms'):
            reforms = test.pop('reforms')
            if not isinstance(reforms, list):
                reforms = [reforms]
            for reform_path in reforms:
                current_tax_benefit_system = current_tax_benefit_system.apply_reform(reform_path)

        try:
            test, error = scenarios.make_json_or_python_to_test(
                tax_benefit_system = current_tax_benefit_system
                )(test)
        except Exception:
            log.error("{} is not a valid OpenFisca test file".format(yaml_path).encode('utf-8'))
            raise

        if error is not None:
            embedding_error = conv.embed_error(test, 'errors', error)
            assert embedding_error is None, embedding_error
            raise ValueError("Error in test {}:\n{}\nYaml test content: \n{}\n".format(
                yaml_path, error, yaml.dump(test, Dumper=Dumper, allow_unicode = True,
                default_flow_style = False, indent = 2, width = 120)))

        yield yaml_path, test.get('name') or filename, to_unicode(test['scenario'].period), test


def _run_test(period_str, test, verbose = False, only_variables = None, ignore_variables = None, options = {}):
    absolute_error_margin = None
    relative_error_margin = None
    if test.get('absolute_error_margin') is not None:
        absolute_error_margin = test.get('absolute_error_margin')
    if test.get('relative_error_margin') is not None:
        relative_error_margin = test.get('relative_error_margin')

    scenario = test['scenario']
    scenario.suggest()
    simulation = scenario.new_simulation(trace = verbose)
    output_variables = test.get('output_variables')
    if output_variables is not None:
        try:
            for variable_name, expected_value in output_variables.items():
                variable_ignored = ignore_variables is not None and variable_name in ignore_variables
                variable_not_tested = only_variables is not None and variable_name not in only_variables
                if variable_ignored or variable_not_tested:
                    continue  # Skip this variable
                if isinstance(expected_value, dict):
                    for requested_period, expected_value_at_period in expected_value.items():
                        assert_near(
                            simulation.calculate(variable_name, requested_period),
                            expected_value_at_period,
                            absolute_error_margin = absolute_error_margin,
                            message = '{}@{}: '.format(variable_name, requested_period),
                            relative_error_margin = relative_error_margin,
                            )
                else:
                    assert_near(
                        simulation.calculate(variable_name),
                        expected_value,
                        absolute_error_margin = absolute_error_margin,
                        message = '{}@{}: '.format(variable_name, period_str),
                        relative_error_margin = relative_error_margin,
                        )
        finally:
            if verbose:
                print("Computation log:")
                simulation.tracer.print_computation_log()
