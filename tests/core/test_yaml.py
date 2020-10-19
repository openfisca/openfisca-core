# -*- coding: utf-8 -*-

import os
import subprocess
import pkg_resources

import pytest
import openfisca_extension_template

from openfisca_core.tools.test_runner import run_tests

from .test_countries import tax_benefit_system


openfisca_core_dir = pkg_resources.get_distribution('OpenFisca-Core').location
yaml_tests_dir = os.path.join(openfisca_core_dir, 'tests', 'core', 'yaml_tests')
EXIT_OK = 0
EXIT_TESTSFAILED = 1


def run_yaml_test(path, options = None):
    yaml_path = os.path.join(yaml_tests_dir, path)

    if options is None:
        options = {}

    result = run_tests(tax_benefit_system, yaml_path, options)
    return result


def test_success():
    assert run_yaml_test('test_success.yml') == EXIT_OK


def test_fail():
    assert run_yaml_test('test_failure.yaml') == EXIT_TESTSFAILED


def test_relative_error_margin_success():
    assert run_yaml_test('test_relative_error_margin.yaml') == EXIT_OK


def test_relative_error_margin_fail():
    assert run_yaml_test('failing_test_relative_error_margin.yaml') == EXIT_TESTSFAILED


def test_absolute_error_margin_success():
    assert run_yaml_test('test_absolute_error_margin.yaml') == EXIT_OK


def test_absolute_error_margin_fail():
    assert run_yaml_test('failing_test_absolute_error_margin.yaml') == EXIT_TESTSFAILED


def test_run_tests_from_directory():
    dir_path = os.path.join(yaml_tests_dir, 'directory')
    assert run_yaml_test(dir_path) == EXIT_OK


def test_with_reform():
    assert run_yaml_test('test_with_reform.yaml') == EXIT_OK


def test_with_extension():
    assert run_yaml_test('test_with_extension.yaml') == EXIT_OK


def test_with_anchors():
    assert run_yaml_test('test_with_anchors.yaml') == EXIT_OK


def test_run_tests_from_directory_fail():
    assert run_yaml_test(yaml_tests_dir) == EXIT_TESTSFAILED


def test_name_filter():
    assert run_yaml_test(
        yaml_tests_dir,
        options = {'name_filter': 'success'}
        ) == EXIT_OK


def test_shell_script():
    yaml_path = os.path.join(yaml_tests_dir, 'test_success.yml')
    command = ['openfisca', 'test', yaml_path, '-c', 'openfisca_country_template']
    with open(os.devnull, 'wb') as devnull:
        subprocess.check_call(command, stdout = devnull, stderr = devnull)


def test_failing_shell_script():
    yaml_path = os.path.join(yaml_tests_dir, 'test_failure.yaml')
    command = ['openfisca', 'test', yaml_path, '-c', 'openfisca_dummy_country']
    with open(os.devnull, 'wb') as devnull:
        with pytest.raises(subprocess.CalledProcessError):
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
