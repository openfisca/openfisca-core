# -*- coding: utf-8 -*-

import pkg_resources
import os
import sys
import subprocess

from nose.tools import nottest, raises
import openfisca_extension_template

from openfisca_core.tools.test_runner import run_tests, generate_tests

from .test_countries import tax_benefit_system


openfisca_core_dir = pkg_resources.get_distribution('OpenFisca-Core').location
yaml_tests_dir = os.path.join(openfisca_core_dir, 'tests', 'core', 'yaml_tests')


# Declare that these two functions are not tests to run with nose
nottest(run_tests)
nottest(generate_tests)


@nottest
def run_yaml_test(path, options = {}):
    yaml_path = os.path.join(yaml_tests_dir, path)

    # We are testing tests, and don't want the latter to print anything, so we temporarily deactivate stderr.
    sys.stderr = open(os.devnull, 'w')
    result = run_tests(tax_benefit_system, yaml_path, options)
    return result


def test_success():
    assert run_yaml_test('test_success.yaml')


def test_fail():
    assert run_yaml_test('test_failure.yaml') is False


def test_relative_error_margin_success():
    assert run_yaml_test('test_relative_error_margin.yaml')


def test_relative_error_margin_fail():
    assert run_yaml_test('failing_test_relative_error_margin.yaml') is False


def test_absolute_error_margin_success():
    assert run_yaml_test('test_absolute_error_margin.yaml')


def test_absolute_error_margin_fail():
    assert run_yaml_test('failing_test_absolute_error_margin.yaml') is False


def test_run_tests_from_directory():
    dir_path = os.path.join(yaml_tests_dir, 'directory')
    assert run_yaml_test(dir_path)


def test_with_reform():
    assert run_yaml_test('test_with_reform.yaml')


def test_with_extension():
    assert run_yaml_test('test_with_extension.yaml')


def test_with_anchors():
    assert run_yaml_test('test_with_anchors.yaml')


def test_run_tests_from_directory_fail():
    assert run_yaml_test(yaml_tests_dir) is False


def test_name_filter():
    assert run_yaml_test(
        yaml_tests_dir,
        options = {'name_filter': 'success'}
        )


def test_shell_script():
    yaml_path = os.path.join(yaml_tests_dir, 'test_success.yaml')
    command = ['openfisca', 'test', yaml_path, '-c', 'openfisca_country_template']
    with open(os.devnull, 'wb') as devnull:
        subprocess.check_call(command, stdout = devnull, stderr = devnull)


@raises(subprocess.CalledProcessError)
def test_failing_shell_script():
    yaml_path = os.path.join(yaml_tests_dir, 'test_failure.yaml')
    command = ['openfisca', 'test', yaml_path, '-c', 'openfisca_dummy_country']
    with open(os.devnull, 'wb') as devnull:
        subprocess.check_call(command, stdout = devnull, stderr = devnull)


def test_shell_script_with_reform():
    yaml_path = os.path.join(yaml_tests_dir, 'test_with_reform_2.yaml')
    command = ['openfisca', 'test', yaml_path, '-c', 'openfisca_country_template', '-r', 'openfisca_country_template.reforms.removal_basic_income.removal_basic_income']
    with open(os.devnull, 'wb') as devnull:
        subprocess.check_call(command, stdout = devnull, stderr = devnull)


def test_shell_script_with_extension():
    tests_dir = os.path.join(openfisca_extension_template.__path__[0], 'tests')
    command = ['openfisca', 'test', tests_dir, '-c', 'openfisca_country_template', '-e', 'openfisca_extension_template']
    with open(os.devnull, 'wb') as devnull:
        subprocess.check_call(command, stdout = devnull, stderr = devnull)
