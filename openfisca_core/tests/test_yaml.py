# -*- coding: utf-8 -*-

import pkg_resources
import os
from nose.tools import nottest, raises

from openfisca_core.test_runner import run_tests_from_yaml_file

from openfisca_core.tests.dummy_country import DummyTaxBenefitSystem

tax_benefit_system = DummyTaxBenefitSystem()

openfisca_core_dir = pkg_resources.get_distribution('OpenFisca-Core').location
yamls_tests_dir = os.path.join(openfisca_core_dir, 'openfisca_core', 'tests', 'tests_yaml')

nottest(run_tests_from_yaml_file)
@nottest
def run_yaml_test(file_name, options = {}):
    yaml_path = os.path.join(yamls_tests_dir, '{}.yaml'.format(file_name))
    run_tests_from_yaml_file(tax_benefit_system, yaml_path, options)

def test_sucess():
    run_yaml_test('test_sucess')

@raises(AssertionError)
def test_fail():
    run_yaml_test('test_failure')

def test_ignore_test():
    run_yaml_test('test_ignore')

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
