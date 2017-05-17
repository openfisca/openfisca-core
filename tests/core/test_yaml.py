# -*- coding: utf-8 -*-

import pkg_resources
import os
import subprocess

from nose.tools import nottest, raises
import openfisca_extension_template
from openfisca_country_template import CountryTaxBenefitSystem

from openfisca_core.tools.test_runner import run_tests, generate_tests

tax_benefit_system = CountryTaxBenefitSystem()


openfisca_core_dir = pkg_resources.get_distribution('OpenFisca-Core').location
yaml_tests_dir = os.path.join(openfisca_core_dir, 'tests', 'core', 'yaml_tests')

# When tests are run by the CI, openfisca_core is not installed in editable mode, therefore the tests are not packaged with the ditribution. We thus get them from ~/openfisca-core/tests/core/yaml_tests
if not os.path.isdir(yaml_tests_dir):
    ci_yaml_tests_dir = os.path.join(os.path.expanduser('~'), 'openfisca-core', 'tests', 'core', 'yaml_tests')
    yaml_tests_dir = ci_yaml_tests_dir if os.path.isdir(ci_yaml_tests_dir) else yaml_tests_dir


# Declare that these two functions are not tests to run with nose
nottest(run_tests)
nottest(generate_tests)


@nottest
def run_yaml_test(file_name, options = {}):
    yaml_path = os.path.join(yaml_tests_dir, '{}.yaml'.format(file_name))
    return run_tests(tax_benefit_system, yaml_path, options)


def test_success():
    run_yaml_test('test_success')


@raises(AssertionError)
def test_fail():
    run_yaml_test('test_failure')


def test_relative_error_margin_success():
    run_yaml_test('test_relative_error_margin')


@raises(AssertionError)
def test_relative_error_margin_fail():
    run_yaml_test('failing_test_relative_error_margin')


def test_absolute_error_margin_success():
    run_yaml_test('test_absolute_error_margin')


@raises(AssertionError)
def test_absolute_error_margin_fail():
    run_yaml_test('failing_test_absolute_error_margin')


def test_run_tests_from_directory():
    dir_path = os.path.join(yaml_tests_dir, 'directory')
    assert run_tests(tax_benefit_system, dir_path) == 4


def test_with_reform():
    run_yaml_test('test_with_reform')


@raises(AssertionError)
def test_run_tests_from_directory_fail():
    run_tests(tax_benefit_system, yaml_tests_dir)


def test_name_filter():
    nb_tests = run_tests(
        tax_benefit_system,
        yaml_tests_dir,
        options = {'name_filter': 'success'}
        )

    assert nb_tests == 3


def test_nose_style():
    dir_path = os.path.join(yaml_tests_dir, 'directory')
    for test in generate_tests(tax_benefit_system, dir_path):
        yield test


def test_shell_script():
    yaml_path = os.path.join(yaml_tests_dir, 'test_success.yaml')
    command = ['openfisca-run-test', yaml_path, '-c', 'openfisca_country_template']
    with open(os.devnull, 'wb') as devnull:
        subprocess.check_call(command, stdout = devnull)


def test_shell_script_with_reform():
    yaml_path = os.path.join(yaml_tests_dir, 'test_with_reform_2.yaml')
    command = ['openfisca-run-test', yaml_path, '-c', 'openfisca_country_template', '-r', 'openfisca_country_template.reforms.removal_basic_income.removal_basic_income']
    with open(os.devnull, 'wb') as devnull:
        subprocess.check_call(command, stdout = devnull)


def test_shell_script_with_extension():
    extension_dir = openfisca_extension_template.__path__[0]
    command = ['openfisca-run-test', extension_dir, '-c', 'openfisca_country_template', '-e', extension_dir]
    with open(os.devnull, 'wb') as devnull:
        subprocess.check_call(command, stdout = devnull)
