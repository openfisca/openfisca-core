# -*- coding: utf-8 -*-

import logging
import sys
import os
import traceback
import textwrap
from typing import Dict, List

import pytest

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

_tax_benefit_system_cache: Dict = {}


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
    +-------------------------------+-----------+ See :any:`openfisca_test` options doc +
    | name_filter                   | ``str``   |                                           |
    +-------------------------------+-----------+-------------------------------------------+

    """

    argv = ["--capture", "no"]

    if options.get('pdb'):
        argv.append('--pdb')

    if isinstance(paths, str):
        paths = [paths]

    if options is None:
        options = {}

    return pytest.main([*argv, *paths] if True else paths, plugins = [OpenFiscaPlugin(tax_benefit_system, options)])


class YamlFile(pytest.File):

    def __init__(self, path, fspath, parent, tax_benefit_system, options):
        super(YamlFile, self).__init__(path, parent)
        self.tax_benefit_system = tax_benefit_system
        self.options = options

    def collect(self):
        try:
            tests = yaml.load(self.fspath.open(), Loader = Loader)
        except (yaml.scanner.ScannerError, yaml.parser.ParserError, TypeError):
            message = os.linesep.join([
                traceback.format_exc(),
                f"'{self.fspath}' is not a valid YAML file. Check the stack trace above for more details.",
                ])
            raise ValueError(message)

        if not isinstance(tests, list):
            tests: List[Dict] = [tests]

        for test in tests:
            if not self.should_ignore(test):
                yield YamlItem.from_parent(self,
                    name = '',
                    baseline_tax_benefit_system = self.tax_benefit_system,
                    test = test, options = self.options)

    def should_ignore(self, test):
        name_filter = self.options.get('name_filter')
        return (
            name_filter is not None
            and name_filter not in os.path.splitext(self.fspath.basename)[0]
            and name_filter not in test.get('name', '')
            and name_filter not in test.get('keywords', [])
            )


class YamlItem(pytest.Item):
    """
    Terminal nodes of the test collection tree.
    """

    def __init__(self, name, parent, baseline_tax_benefit_system, test, options):
        super(YamlItem, self).__init__(name, parent)
        self.baseline_tax_benefit_system = baseline_tax_benefit_system
        self.options = options
        self.test = test
        self.simulation = None
        self.tax_benefit_system = None

    def runtest(self):
        self.name = self.test.get('name', '')
        if not self.test.get('output'):
            raise ValueError("Missing key 'output' in test '{}' in file '{}'".format(self.name, self.fspath))

        if not TEST_KEYWORDS.issuperset(self.test.keys()):
            unexpected_keys = set(self.test.keys()).difference(TEST_KEYWORDS)
            raise ValueError("Unexpected keys {} in test '{}' in file '{}'".format(unexpected_keys, self.name, self.fspath))

        self.tax_benefit_system = _get_tax_benefit_system(self.baseline_tax_benefit_system, self.test.get('reforms', []), self.test.get('extensions', []))

        builder = SimulationBuilder()
        input = self.test.get('input', {})
        period = self.test.get('period')
        verbose = self.options.get('verbose')
        performance_graph = self.options.get('performance_graph')
        performance_tables = self.options.get('performance_tables')

        try:
            builder.set_default_period(period)
            self.simulation = builder.build_from_dict(self.tax_benefit_system, input)
        except (VariableNotFound, SituationParsingError):
            raise
        except Exception as e:
            error_message = os.linesep.join([str(e), '', f"Unexpected error raised while parsing '{self.fspath}'"])
            raise ValueError(error_message).with_traceback(sys.exc_info()[2]) from e  # Keep the stack trace from the root error

        try:
            self.simulation.trace = verbose or performance_graph or performance_tables
            self.check_output()
        finally:
            tracer = self.simulation.tracer
            if verbose:
                self.print_computation_log(tracer)
            if performance_graph:
                self.generate_performance_graph(tracer)
            if performance_tables:
                self.generate_performance_tables(tracer)

    def print_computation_log(self, tracer):
        print("Computation log:")  # noqa T001
        tracer.print_computation_log()

    def generate_performance_graph(self, tracer):
        tracer.generate_performance_graph('.')

    def generate_performance_tables(self, tracer):
        tracer.generate_performance_tables('.')

    def check_output(self):
        output = self.test.get('output')

        if output is None:
            return
        for key, expected_value in output.items():
            if self.tax_benefit_system.get_variable(key):  # If key is a variable
                self.check_variable(key, expected_value, self.test.get('period'))
            elif self.simulation.populations.get(key):  # If key is an entity singular
                for variable_name, value in expected_value.items():
                    self.check_variable(variable_name, value, self.test.get('period'))
            else:
                population = self.simulation.get_population(plural = key)
                if population is not None:  # If key is an entity plural
                    for instance_id, instance_values in expected_value.items():
                        for variable_name, value in instance_values.items():
                            entity_index = population.get_index(instance_id)
                            self.check_variable(variable_name, value, self.test.get('period'), entity_index)
                else:
                    raise VariableNotFound(key, self.tax_benefit_system)

    def check_variable(self, variable_name, expected_value, period, entity_index = None):
        if self.should_ignore_variable(variable_name):
            return
        if isinstance(expected_value, dict):
            for requested_period, expected_value_at_period in expected_value.items():
                self.check_variable(variable_name, expected_value_at_period, requested_period, entity_index)
            return

        actual_value = self.simulation.calculate(variable_name, period)

        if entity_index is not None:
            actual_value = actual_value[entity_index]
        return assert_near(
            actual_value,
            expected_value,
            absolute_error_margin = self.test.get('absolute_error_margin'),
            message = f"{variable_name}@{period}: ",
            relative_error_margin = self.test.get('relative_error_margin'),
            )

    def should_ignore_variable(self, variable_name):
        only_variables = self.options.get('only_variables')
        ignore_variables = self.options.get('ignore_variables')
        variable_ignored = ignore_variables is not None and variable_name in ignore_variables
        variable_not_tested = only_variables is not None and variable_name not in only_variables

        return variable_ignored or variable_not_tested

    def repr_failure(self, excinfo):
        if not isinstance(excinfo.value, (AssertionError, VariableNotFound, SituationParsingError)):
            return super(YamlItem, self).repr_failure(excinfo)

        message = excinfo.value.args[0]
        if isinstance(excinfo.value, SituationParsingError):
            message = f"Could not parse situation described: {message}"

        return os.linesep.join([
            f"{str(self.fspath)}:",
            f"  Test '{str(self.name)}':",
            textwrap.indent(message, '    ')
            ])


class OpenFiscaPlugin(object):

    def __init__(self, tax_benefit_system, options):
        self.tax_benefit_system = tax_benefit_system
        self.options = options

    def pytest_collect_file(self, parent, path):
        """
        Called by pytest for all plugins.
        :return: The collector for test methods.
        """
        if path.ext in [".yaml", ".yml"]:
            return YamlFile.from_parent(parent, path = path, fspath = path,
                tax_benefit_system = self.tax_benefit_system,
                options = self.options)


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
