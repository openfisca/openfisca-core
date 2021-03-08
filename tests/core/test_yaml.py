# -*- coding: utf-8 -*-

import pkg_resources
import os
import subprocess

from pytest import mark, raises

import openfisca_extension_template

from openfisca_core.tools.test_runner import run_tests

from .test_countries import tax_benefit_system


openfisca_core_dir = pkg_resources.get_distribution('OpenFisca-Core').location
yaml_tests_dir = os.path.join(openfisca_core_dir, 'tests', 'core', 'yaml_tests')
EXIT_OK = 0
EXIT_TESTSFAILED = 1


@mark.parametrize("path, options, expected", [
    ("test_success.yaml", {}, EXIT_OK),
    ("test_failure.yaml", {}, EXIT_TESTSFAILED),
    ("test_relative_error_margin.yaml", {}, EXIT_OK),
    ("failing_test_relative_error_margin.yaml", {}, EXIT_TESTSFAILED),
    ("test_absolute_error_margin.yaml", {}, EXIT_OK),
    ("failing_test_absolute_error_margin.yaml", {}, EXIT_TESTSFAILED),
    (os.path.join(yaml_tests_dir, "directory"), {}, EXIT_OK),
    ("test_with_reform.yaml", {}, EXIT_OK),
    ("test_with_extension.yaml", {}, EXIT_OK),
    ("test_with_anchors.yaml", {}, EXIT_OK),
    (yaml_tests_dir, {}, EXIT_TESTSFAILED),
    (yaml_tests_dir, {"name_filter": "success"}, EXIT_OK),
    ])
def test_yaml(path, options, expected):
    yaml_path = os.path.join(yaml_tests_dir, path)
    result = run_tests(tax_benefit_system, yaml_path, options)
    assert result == expected


def test_shell_script():
    yaml_path = os.path.join(yaml_tests_dir, 'test_success.yaml')
    command = ['openfisca', 'test', yaml_path, '-c', 'openfisca_country_template']
    with open(os.devnull, 'wb') as devnull:
        subprocess.check_call(command, stdout = devnull, stderr = devnull)


def test_failing_shell_script():
    yaml_path = os.path.join(yaml_tests_dir, 'test_failure.yaml')
    command = ['openfisca', 'test', yaml_path, '-c', 'openfisca_dummy_country']
    with open(os.devnull, 'wb') as devnull:
        with raises(subprocess.CalledProcessError):
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
