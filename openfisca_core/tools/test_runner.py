# -*- coding: utf-8 -*-

"""
A module to run openfisca yaml tests
"""

from builtins import str

import glob
import os
import sys
import unittest
import logging
import traceback

import nose

from openfisca_core.tools import assert_near
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_core.errors import SituationParsingError, VariableNotFound


log = logging.getLogger(__name__)


def import_yaml():
    import yaml
    try:
        from yaml import CLoader as Loader
    except ImportError:
        log.warning(
            ' '
            'libyaml is not installed in your environment, this can make your '
            'test suite slower to run. Once you have installed libyaml, run `pip '
            'uninstall pyyaml && pip install pyyaml --no-cache-dir` so that it is used in your '
            'Python environment.')
        from yaml import SafeLoader as Loader
    return yaml, Loader


TEST_KEYWORDS = {'absolute_error_margin', 'description', 'extensions', 'ignore_variables', 'input', 'keywords', 'name', 'only_variables', 'output', 'period', 'reforms', 'relative_error_margin'}

yaml, Loader = import_yaml()

_tax_benefit_system_cache = {}


# Exposed methods

def generate_tests(tax_benefit_system, paths, options = None):
    """
    Generates a lazy iterator of all the YAML tests contained in a file or a directory.

    :parameters: Same as :meth:`run_tests`

    :return: a generator of YAML tests

    """

    if isinstance(paths, str):
        paths = [paths]

    if options is None:
        options = {}

    for path in paths:
        if os.path.isdir(path):
            for test in _generate_tests_from_directory(tax_benefit_system, path, options):
                yield test
        else:
            for test in _generate_tests_from_file(tax_benefit_system, path, options):
                yield test


def run_tests(tax_benefit_system, paths, options = None):
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

    if options is None:
        options = {}

    if options.get('pdb'):
        argv.append('--pdb')

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
    verbose = options.get('verbose')

    tests = _parse_test_file(tax_benefit_system, path_to_file, options)

    for _test_index, (simulation, test) in enumerate(tests, 1):
        if name_filter is not None and name_filter not in filename \
                and name_filter not in (test.get('name', '')) \
                and name_filter not in (test.get('keywords', [])):
            continue

        keywords = test.get('keywords', [])
        title = "{}: {}{} - {}".format(
            os.path.basename(path_to_file),
            '[{}] '.format(', '.join(keywords)) if keywords else '',
            test.get('name'),
            test.get('period'),
            )
        test.update({'options': options})

        def check():
            try:
                _run_test(simulation, test)
            except Exception:
                log.error(title)
                raise
            finally:
                if verbose:
                    print("Computation log:")  # noqa T001
                    simulation.tracer.print_computation_log()

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


def _parse_test_file(tax_benefit_system, yaml_path, options):
    with open(yaml_path) as yaml_file:
        try:
            tests = yaml.load(yaml_file, Loader = Loader)
        except (yaml.scanner.ScannerError, TypeError):
            message = os.linesep.join([
                traceback.format_exc(),
                "'{}'' is not a valid YAML file. Check the stack trace above for more details.".format(yaml_path),
                ])
            raise ValueError(message)

    if not isinstance(tests, list):
        tests = [tests]
    tests = filter(lambda test: test, tests)  # Remove empty tests

    for test in tests:
        yield _parse_test(tax_benefit_system, test, options, yaml_path)


def _get_tax_benefit_system(baseline, reforms, extensions):
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


def _parse_test(tax_benefit_system, test, options, yaml_path):
    name = test.get('name', '')
    if not test.get('output'):
        raise ValueError("Missing key 'output' in test '{}' in file '{}'".format(name, yaml_path))

    if not TEST_KEYWORDS.issuperset(test.keys()):
        unexpected_keys = set(test.keys()).difference(TEST_KEYWORDS)
        raise ValueError("Unexpected keys {} in test '{}' in file '{}'".format(unexpected_keys, name, yaml_path))
    test['file_path'] = yaml_path

    current_tax_benefit_system = _get_tax_benefit_system(tax_benefit_system, test.get('reforms', []), test.get('extensions', []))

    try:
        builder = SimulationBuilder()
        input = test.pop('input', {})
        period = test.get('period')
        verbose = options.get('verbose')
        builder.set_default_period(period)
        simulation = builder.build_from_dict(current_tax_benefit_system, input)
        simulation.trace = verbose
    except Exception:
        raise ValueError("Unexpected error while parsing {}".format(test['file_path']))
    except SituationParsingError as error:
        message = os.linesep.join([
            traceback.format_exc(),
            str(error.error),
            os.linesep,
            "Could not parse situation described in test '{}' in YAML file '{}'. Check the stack trace above for more details.".format(name, yaml_path),
            ])
        raise ValueError(message)
    return simulation, test


def _run_test(simulation, test):
    tax_benefit_system = simulation.tax_benefit_system
    output = test.get('output')

    if output is None:
        return
    for key, expected_value in output.items():
        if tax_benefit_system.variables.get(key):  # If key is a variable
            _check_variable(simulation, key, expected_value, test.get('period'), test)
        elif simulation.entities.get(key):  # If key is an entity singular
            for variable_name, value in expected_value.items():
                _check_variable(simulation, variable_name, value, test.get('period'), test)
        else:
            entity_array = simulation.get_entity(plural = key)
            if entity_array is not None:  # If key is an entity plural
                for entity_id, value_by_entity in expected_value.items():
                    for variable_name, value in value_by_entity.items():
                        entity_index = entity_array.ids.index(entity_id)
                        _check_variable(simulation, variable_name, value, test.get('period'), test, entity_index)
            else:
                raise VariableNotFound(key, tax_benefit_system)


def _should_ignore_variable(variable_name, test):
    only_variables = test['options'].get('only_variables')
    ignore_variables = test['options'].get('ignore_variables')
    variable_ignored = ignore_variables is not None and variable_name in ignore_variables
    variable_not_tested = only_variables is not None and variable_name not in only_variables

    return variable_ignored or variable_not_tested


def _check_variable(simulation, variable_name, expected_value, period, test, entity_index = None):
    if _should_ignore_variable(variable_name, test):
        return
    if isinstance(expected_value, dict):
        for requested_period, expected_value_at_period in expected_value.items():
            _check_variable(simulation, variable_name, expected_value_at_period, requested_period, test, entity_index)
        return
    actual_value = simulation.calculate(variable_name, period)
    if entity_index is not None:
        actual_value = actual_value[entity_index]
    return assert_near(
        actual_value,
        expected_value,
        absolute_error_margin = test.get('absolute_error_margin'),
        message = "In test '{}', in file '{}', {}@{}: ".format(
            test.get('name'), test.get('file_path'), variable_name, period),
        relative_error_margin = test.get('relative_error_margin'),
        )
