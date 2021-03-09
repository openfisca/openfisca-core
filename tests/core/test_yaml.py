# -*- coding: utf-8 -*-

import os
import pkg_resources
import subprocess

from pytest import fixture, mark

import openfisca_extension_template

from openfisca_core.tools.test_runner import run_tests

from .test_countries import tax_benefit_system


core_dir = pkg_resources.get_distribution("OpenFisca-Core").location
yaml_dir = os.path.join(core_dir, "tests", "core", "yaml_tests")

EXIT_OK = 0
EXIT_KO = 1


@fixture
def path(request):
    return os.path.join(*request.param)


@fixture
def make_call():
    with open(os.devnull, "wb") as devnull:
        def _make_call(command):
            return subprocess.call(command, stdout = devnull, stderr = devnull)

        yield _make_call


@mark.parametrize("expected, path, options", [
    (EXIT_OK, (yaml_dir, "test_success.yaml"), {}),
    (EXIT_KO, (yaml_dir, "test_failure.yaml"), {}),
    (EXIT_OK, (yaml_dir, "test_relative_error_margin.yaml"), {}),
    (EXIT_KO, (yaml_dir, "failing_test_relative_error_margin.yaml"), {}),
    (EXIT_OK, (yaml_dir, "test_absolute_error_margin.yaml"), {}),
    (EXIT_KO, (yaml_dir, "failing_test_absolute_error_margin.yaml"), {}),
    (EXIT_OK, (yaml_dir, os.path.join(yaml_dir, "directory")), {}),
    (EXIT_OK, (yaml_dir, "test_with_reform.yaml"), {}),
    (EXIT_OK, (yaml_dir, "test_with_extension.yaml"), {}),
    (EXIT_OK, (yaml_dir, "test_with_anchors.yaml"), {}),
    (EXIT_KO, (yaml_dir, yaml_dir), {}),
    (EXIT_OK, (yaml_dir, yaml_dir), {"name_filter": "success"}),
    ], indirect = ["path"])
def test_yaml(path, options, expected):
    result = run_tests(tax_benefit_system, path, options)
    assert result == expected


@mark.parametrize("expected, path, make_command", [
    (EXIT_OK, (yaml_dir, "test_success.yaml"), lambda path: ["openfisca", "test", path, "-c", "openfisca_country_template"]),
    (EXIT_KO, (yaml_dir, "test_failure.yaml"), lambda path: ["openfisca", "test", path, "-c", "openfisca_dummy_country"]),
    (EXIT_OK, (yaml_dir, "test_with_reform_2.yaml"), lambda path: ["openfisca", "test", path, "-c", "openfisca_country_template", "-r", "openfisca_country_template.reforms.removal_basic_income.removal_basic_income"]),
    (EXIT_OK, (openfisca_extension_template.__path__[0], "tests"), lambda path: ["openfisca", "test", path, "-c", "openfisca_country_template", "-e", "openfisca_extension_template"]),
    ], indirect = ["path"])
def test_shell_script(expected, path, make_command, make_call):
    command = make_command(path)
    result = make_call(command)
    assert result == expected
