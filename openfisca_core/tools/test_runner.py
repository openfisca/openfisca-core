# -*- coding: utf-8 -*-

"""
A module to run openfisca yaml tests
"""

import collections
import copy
import glob
import os
import yaml
import numpy as np

from openfisca_core import conv, periods, scenarios
from openfisca_core.tools import assert_near


# Yaml module configuration

def _config_yaml(yaml):

    class folded_unicode(unicode):
        pass

    class literal_unicode(unicode):
        pass

    def dict_constructor(loader, node):
        return collections.OrderedDict(loader.construct_pairs(node))

    yaml.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, dict_constructor)

    yaml.add_representer(collections.OrderedDict, lambda dumper, data: dumper.represent_dict(
        (copy.deepcopy(key), value)
        for key, value in data.iteritems()
        ))
    yaml.add_representer(dict, lambda dumper, data: dumper.represent_dict(
        (copy.deepcopy(key), value)
        for key, value in data.iteritems()
        ))
    yaml.add_representer(folded_unicode, lambda dumper, data: dumper.represent_scalar(u'tag:yaml.org,2002:str',
        data, style='>'))
    yaml.add_representer(literal_unicode, lambda dumper, data: dumper.represent_scalar(u'tag:yaml.org,2002:str',
        data, style='|'))
    yaml.add_representer(np.ndarray, lambda dumper, data: dumper.represent_list(data.tolist()))
    yaml.add_representer(periods.Instant, lambda dumper, data: dumper.represent_scalar(u'tag:yaml.org,2002:str', str(data)))
    yaml.add_representer(periods.Period, lambda dumper, data: dumper.represent_scalar(u'tag:yaml.org,2002:str', str(data)))
    yaml.add_representer(tuple, lambda dumper, data: dumper.represent_list(data))
    yaml.add_representer(unicode, lambda dumper, data: dumper.represent_scalar(u'tag:yaml.org,2002:str', data))

    return yaml


_config_yaml(yaml)


# Exposed methods

def generate_tests(tax_benefit_system, path, options = {}):
    """
    Generates a lazy iterator of all the YAML tests contained in a file or a directory.

    :parameters: Same as :meth:`run_tests`

    :return: a generator of YAML tests

    """

    if os.path.isdir(path):
        return _generate_tests_from_directory(tax_benefit_system, path, options)
    else:
        return _generate_tests_from_file(tax_benefit_system, path, options)


def run_tests(tax_benefit_system, path, options = {}):
    """
    Runs all the YAML tests contained in a file or a directory.

    If `path` is a directory, subdirectories will be recursively explored.

    :param TaxBenefitSystem tax_benefit_system: the tax-benefit system to use to run the tests
    :param str path: the path towards the file or directory containing thes tests. If it is a directory, subdirectories will be recursively explored.
    :param dict options: See more details below.

    :raises AssertionError: if a test does not pass

    :return: the number of sucessful tests excecuted

    **Testing options**:

    +-------------------------------+-----------+-------------------------------------------+
    | Key                           | Type      | Role                                      |
    +===============================+===========+===========================================+
    | force                         | ``bool``  |                                           |
    +-------------------------------+-----------+                                           +
    | verbose                       | ``bool``  |                                           |
    +-------------------------------+-----------+                                           +
    | name_filter                   | ``str``   | See :any:`openfisca-run-test` options doc |
    +-------------------------------+-----------+                                           +
    | default_absolute_error_margin | ``float`` |                                           |
    +-------------------------------+-----------+                                           +
    | default_relative_error_margin | ``float`` |                                           |
    +-------------------------------+-----------+-------------------------------------------+

    """

    nb_tests = 0
    for test in generate_tests(tax_benefit_system, path, options):
        test()
        nb_tests += 1

    return nb_tests  # Nb of sucessful tests


# Internal methods

def _generate_tests_from_file(tax_benefit_system, path_to_file, options = {}):
    filename = os.path.splitext(os.path.basename(path_to_file))[0]
    force = options.get('force')
    name_filter = options.get('name_filter')
    if isinstance(name_filter, str):
        name_filter = name_filter.decode('utf-8')
    verbose = options.get('verbose')

    tests = _parse_yaml_file(tax_benefit_system, path_to_file)

    for test_index, (path_to_file, name, period_str, test) in enumerate(tests, 1):

        if not force and test.get(u'ignore', False):
            continue
        if name_filter is not None and name_filter not in filename \
                and name_filter not in (test.get('name', u'')) \
                and name_filter not in (test.get('keywords', [])):
            continue

        keywords = test.get('keywords', [])
        title = "{}: {}{} - {}".format(
            os.path.basename(path_to_file),
            u'[{}] '.format(u', '.join(keywords)).encode('utf-8') if keywords else '',
            name.encode('utf-8'),
            period_str,
            )

        def check():
            print("=" * len(title))
            print(title)
            print("=" * len(title))
            _run_test(period_str, test, verbose, options)

        yield check


def _generate_tests_from_directory(tax_benefit_system, path_to_dir, options = {}):
    yaml_paths = glob.glob(os.path.join(path_to_dir, "*.yaml"))
    subdirectories = glob.glob(os.path.join(path_to_dir, "*/"))

    for yaml_path in yaml_paths:
        for test in _generate_tests_from_file(tax_benefit_system, yaml_path, options):
            yield test

    for subdirectory in subdirectories:
        for test in _generate_tests_from_directory(tax_benefit_system, subdirectory, options):
            yield test


def _parse_yaml_file(tax_benefit_system, yaml_path):
    filename = os.path.splitext(os.path.basename(yaml_path))[0]
    with open(yaml_path) as yaml_file:
        tests = yaml.load(yaml_file)

    tests, error = conv.pipe(
        conv.make_item_to_singleton(),
        conv.uniform_sequence(
            conv.noop,
            drop_none_items = True,
            ),
        )(tests)

    if error is not None:
        embedding_error = conv.embed_error(tests, u'errors', error)
        assert embedding_error is None, embedding_error
        raise ValueError("Error in test {}:\n{}".format(yaml_path, yaml.dump(tests, allow_unicode = True,
            default_flow_style = False, indent = 2, width = 120)))

    for test in tests:
        test, error = scenarios.make_json_or_python_to_test(
            tax_benefit_system = tax_benefit_system
            )(test)

        if error is not None:
            embedding_error = conv.embed_error(test, u'errors', error)
            assert embedding_error is None, embedding_error
            raise ValueError("Error in test {}:\n{}\nYaml test content: \n{}\n".format(
                yaml_path, error, yaml.dump(test, allow_unicode = True,
                default_flow_style = False, indent = 2, width = 120)))

        yield yaml_path, test.get('name') or filename, unicode(test['scenario'].period), test


def _run_test(period_str, test, verbose = False, options = {}):
    absolute_error_margin = None
    relative_error_margin = None
    if test.get('absolute_error_margin') is not None:
        absolute_error_margin = test.get('absolute_error_margin')
    if test.get('relative_error_margin') is not None:
        relative_error_margin = test.get('relative_error_margin')
    if absolute_error_margin is None and relative_error_margin is None:
        absolute_error_margin = options.get('default_absolute_error_margin')
        relative_error_margin = options.get('default_relative_error_margin')

    scenario = test['scenario']
    scenario.suggest()
    simulation = scenario.new_simulation(debug = verbose)
    output_variables = test.get(u'output_variables')
    if output_variables is not None:
        output_variables_name_to_ignore = test.get(u'output_variables_name_to_ignore') or set()
        for variable_name, expected_value in output_variables.iteritems():
            if not options.get('force') and variable_name in output_variables_name_to_ignore:
                continue
            if isinstance(expected_value, dict):
                for requested_period, expected_value_at_period in expected_value.iteritems():
                    assert_near(
                        simulation.calculate(variable_name, requested_period),
                        expected_value_at_period,
                        absolute_error_margin = absolute_error_margin,
                        message = u'{}@{}: '.format(variable_name, requested_period),
                        relative_error_margin = relative_error_margin,
                        )
            else:
                assert_near(
                    simulation.calculate(variable_name),
                    expected_value,
                    absolute_error_margin = absolute_error_margin,
                    message = u'{}@{}: '.format(variable_name, period_str),
                    relative_error_margin = relative_error_margin,
                    )
