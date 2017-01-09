# -*- coding: utf-8 -*-

import pkg_resources
import os
from nose.tools import nottest, raises

from openfisca_core.test_runner import run_tests, generate_tests

from openfisca_core.tests.dummy_country import DummyTaxBenefitSystem

tax_benefit_system = DummyTaxBenefitSystem()

openfisca_core_dir = pkg_resources.get_distribution('OpenFisca-Core').location
yamls_tests_dir = os.path.join(openfisca_core_dir, 'openfisca_core', 'tests', 'tests_yaml')

# Declare that these two functions are not tests to run with nose
nottest(run_tests)
nottest(generate_tests)


@nottest
def run_yaml_test(file_name, options = {}):
    yaml_path = os.path.join(yamls_tests_dir, '{}.yaml'.format(file_name))
    return run_tests(tax_benefit_system, yaml_path, options)


def test_success():
    run_yaml_test('test_success')


@raises(AssertionError)
def test_fail():
    run_yaml_test('test_failure')


def test_ignore_test():
    # The 2nd test is ignored
    assert run_yaml_test('test_ignore') == 1


@raises(AssertionError)
def test_force():
    run_yaml_test('test_ignore', options = {'force': True})


def test_relative_error_margin_success():
    run_yaml_test('test_relative_error_margin')


@raises(AssertionError)
def test_relative_error_margin_fail():
    run_yaml_test('test_relative_error_margin', options = {'force': True})


def test_absolute_error_margin_success():
    run_yaml_test('test_absolute_error_margin')


@raises(AssertionError)
def test_absolute_error_margin_fail():
    run_yaml_test('test_absolute_error_margin', options = {'force': True})


def test_run_tests_from_directory():
    dir_path = os.path.join(yamls_tests_dir, 'directory')
    assert run_tests(tax_benefit_system, dir_path) == 5


@raises(AssertionError)
def test_run_tests_from_directory_fail():
    dir_path = os.path.join(yamls_tests_dir, 'directory')
    run_tests(tax_benefit_system, dir_path, options = {'force': True})


def test_name_filter():
    nb_tests = run_tests(
        tax_benefit_system,
        yamls_tests_dir,
        options = {'name_filter': 'success'}
        )

    assert nb_tests == 3


def test_nose_style():
    dir_path = os.path.join(yamls_tests_dir, 'directory')
    for test in generate_tests(tax_benefit_system, dir_path):
        yield test
