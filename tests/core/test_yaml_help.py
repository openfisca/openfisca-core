# -*- coding: utf-8 -*-

import pkg_resources
import os
import sys

from nose.tools import nottest

from openfisca_core.tools.test_runner import run_tests

from .test_countries import tax_benefit_system


openfisca_core_dir = pkg_resources.get_distribution('OpenFisca-Core').location
yaml_tests_dir = os.path.join(openfisca_core_dir, 'tests', 'core', 'yaml_tests')


# Declare that this function is not a test to run with nose
nottest(run_tests)


@nottest
def run_yaml_test(path, options = {}):
    yaml_path = os.path.join(yaml_tests_dir, path)

    result = run_tests(tax_benefit_system, yaml_path, options)
    return result


def test_fail():
    assert run_yaml_test('test_failure_help_message.yaml') is False
    sys.stderr.seek(0)
    helpMessage = sys.stderr.read()
    assert b'income_tax@2015-02:' in helpMessage
