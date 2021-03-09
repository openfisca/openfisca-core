import os
from pkg_resources import get_distribution

from pytest import fixture, mark

from openfisca_core.tools.test_runner import run_tests

from tests.core.test_countries import tax_benefit_system

core_dir = get_distribution("OpenFisca-Core").location
yaml_dir = os.path.join(core_dir, "tests", "core", "yaml_tests")

EXIT_OK = 0
EXIT_KO = 1


@fixture
def path(request):
    return os.path.join(*request.param)


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
def test_yaml(expected, path, options):
    result = run_tests(tax_benefit_system, path, options)
    assert result == expected
