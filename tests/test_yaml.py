# -*- coding: utf-8 -*-

import pkg_resources
import os
import subprocess
from nose.tools import nottest, raises

from openfisca_core.tools.test_runner import run_tests, generate_tests

from openfisca_dummy_country import DummyTaxBenefitSystem

tax_benefit_system = DummyTaxBenefitSystem()

openfisca_dummy_country_dir = pkg_resources.get_distribution('OpenFisca-Dummy-Country').location
yamls_tests_dir = os.path.join(openfisca_dummy_country_dir, 'openfisca_dummy_country', 'tests')

# Declare that these two functions are not tests to run with nose
nottest(run_tests)
nottest(generate_tests)


@nottest
def run_yaml_test(file_name, options = {}):
    yaml_path = os.path.join(yamls_tests_dir, '{}.yaml'.format(file_name))
    return run_tests(tax_benefit_system, yaml_path, options)


def test_success():
    run_yaml_test('test_success', options = {'default_absolute_error_margin': 0.01})


@raises(AssertionError)
def test_fail():
    run_yaml_test('test_failure', options = {'default_absolute_error_margin': 0.01})


def test_relative_error_margin_success():
    run_yaml_test('test_relative_error_margin', options = {'default_absolute_error_margin': 0.01})


@raises(AssertionError)
def test_relative_error_margin_fail():
    run_yaml_test('failing_test_relative_error_margin', options = {'default_absolute_error_margin': 0.01})


def test_absolute_error_margin_success():
    run_yaml_test('test_absolute_error_margin', options = {'default_absolute_error_margin': 0.01})


@raises(AssertionError)
def test_absolute_error_margin_fail():
    run_yaml_test('failing_test_absolute_error_margin', options = {'default_absolute_error_margin': 0.01})


def test_run_tests_from_directory():
    dir_path = os.path.join(yamls_tests_dir, 'directory')
    assert run_tests(tax_benefit_system, dir_path, options = {'default_absolute_error_margin': 0.01}) == 5


def test_with_reform():
    run_yaml_test('test_with_reform', options = {'default_absolute_error_margin': 0.01})


@raises(AssertionError)
def test_run_tests_from_directory_fail():
    run_tests(tax_benefit_system, yamls_tests_dir, options = {'default_absolute_error_margin': 0.01})


def test_name_filter():
    nb_tests = run_tests(
        tax_benefit_system,
        yamls_tests_dir,
        options = {'name_filter': 'success', 'default_absolute_error_margin': 0.01}
        )

    assert nb_tests == 3


def test_nose_style():
    dir_path = os.path.join(yamls_tests_dir, 'directory')
    for test in generate_tests(tax_benefit_system, dir_path, options = {'default_absolute_error_margin': 0.01}):
        yield test


def test_shell_script():
    yaml_path = os.path.join(yamls_tests_dir, 'test_success.yaml')
    command = ['openfisca-run-test', yaml_path, '-c', 'openfisca_dummy_country']
    with open(os.devnull, 'wb') as devnull:
        subprocess.check_call(command, stdout = devnull)


def test_shell_script_with_reform():
    yaml_path = os.path.join(yamls_tests_dir, 'test_with_reform_2.yaml')
    command = ['openfisca-run-test', yaml_path, '-c', 'openfisca_dummy_country', '-r', 'openfisca_dummy_country.dummy_reforms.neutralization_rsa']
    with open(os.devnull, 'wb') as devnull:
        subprocess.check_call(command, stdout = devnull)


def test_shell_script_with_extension():
    extension_dir = os.path.join(openfisca_dummy_country_dir, 'openfisca_dummy_country', 'dummy_extension')
    command = ['openfisca-run-test', extension_dir, '-c', 'openfisca_dummy_country', '-e', extension_dir]
    with open(os.devnull, 'wb') as devnull:
        subprocess.check_call(command, stdout = devnull)
