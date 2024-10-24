import os
import pathlib
import subprocess

import pytest

import openfisca_extension_template

from openfisca_core.tools.test_runner import run_tests
from tests.fixtures import yaml_tests

yaml_tests_dir = os.path.dirname(yaml_tests.__file__)
EXIT_OK = 0
EXIT_TESTSFAILED = 1


def run_yaml_test(tax_benefit_system, path, options=None):
    yaml_path = os.path.join(yaml_tests_dir, path)

    if options is None:
        options = {}

    return run_tests(tax_benefit_system, yaml_path, options)


def test_success(tax_benefit_system) -> None:
    assert run_yaml_test(tax_benefit_system, "test_success.yml") == EXIT_OK


def test_fail(tax_benefit_system) -> None:
    assert run_yaml_test(tax_benefit_system, "test_failure.yaml") == EXIT_TESTSFAILED


def test_relative_error_margin_success(tax_benefit_system) -> None:
    assert (
        run_yaml_test(tax_benefit_system, "test_relative_error_margin.yaml") == EXIT_OK
    )


def test_relative_error_margin_fail(tax_benefit_system) -> None:
    assert (
        run_yaml_test(tax_benefit_system, "failing_test_relative_error_margin.yaml")
        == EXIT_TESTSFAILED
    )


def test_absolute_error_margin_success(tax_benefit_system) -> None:
    assert (
        run_yaml_test(tax_benefit_system, "test_absolute_error_margin.yaml") == EXIT_OK
    )


def test_absolute_error_margin_fail(tax_benefit_system) -> None:
    assert (
        run_yaml_test(tax_benefit_system, "failing_test_absolute_error_margin.yaml")
        == EXIT_TESTSFAILED
    )


def test_run_tests_from_directory(tax_benefit_system) -> None:
    dir_path = os.path.join(yaml_tests_dir, "directory")
    assert run_yaml_test(tax_benefit_system, dir_path) == EXIT_OK


def test_with_reform(tax_benefit_system) -> None:
    assert run_yaml_test(tax_benefit_system, "test_with_reform.yaml") == EXIT_OK


def test_with_extension(tax_benefit_system) -> None:
    assert run_yaml_test(tax_benefit_system, "test_with_extension.yaml") == EXIT_OK


def test_with_anchors(tax_benefit_system) -> None:
    assert run_yaml_test(tax_benefit_system, "test_with_anchors.yaml") == EXIT_OK


def test_run_tests_from_directory_fail(tax_benefit_system) -> None:
    assert run_yaml_test(tax_benefit_system, yaml_tests_dir) == EXIT_TESTSFAILED


def test_name_filter(tax_benefit_system) -> None:
    assert (
        run_yaml_test(
            tax_benefit_system,
            yaml_tests_dir,
            options={"name_filter": "success"},
        )
        == EXIT_OK
    )


def test_shell_script() -> None:
    yaml_path = os.path.join(yaml_tests_dir, "test_success.yml")
    command = ["openfisca", "test", yaml_path, "-c", "openfisca_country_template"]
    result = subprocess.run(command, capture_output=True)
    assert result.returncode == 0, result.stderr.decode("utf-8")


def test_failing_shell_script() -> None:
    yaml_path = os.path.join(yaml_tests_dir, "test_failure.yaml")
    command = ["openfisca", "test", yaml_path, "-c", "openfisca_dummy_country"]
    with open(os.devnull, "wb") as devnull:
        with pytest.raises(subprocess.CalledProcessError):
            subprocess.check_call(command, stdout=devnull, stderr=devnull)


def test_shell_script_with_reform() -> None:
    yaml_path = os.path.join(yaml_tests_dir, "test_with_reform_2.yaml")
    command = [
        "openfisca",
        "test",
        yaml_path,
        "-c",
        "openfisca_country_template",
        "-r",
        "openfisca_country_template.reforms.removal_basic_income.removal_basic_income",
    ]
    result = subprocess.run(command, capture_output=True)
    assert result.returncode == 0, result.stderr.decode("utf-8")


def test_shell_script_with_extension() -> None:
    base_path = next(iter(openfisca_extension_template.__path__))
    test_path = (
        pathlib.Path(base_path) / ".." / "tests" / "openfisca_extension_template"
    )
    path = str(test_path.resolve())
    command = [
        "openfisca",
        "test",
        path,
        "-c",
        "openfisca_country_template",
        "-e",
        "openfisca_extension_template",
    ]
    result = subprocess.run(command, capture_output=True)
    assert not result.stderr, result.stderr.decode("utf-8")
