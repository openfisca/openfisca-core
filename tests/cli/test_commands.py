from click.testing import CliRunner
from pytest import fixture

from openfisca_cli.commands import openfisca, serve, test


@fixture
def runner():
    return CliRunner()


def test_openfisca(runner):
    result = runner.invoke(openfisca)
    assert result.exit_code == 0


def test_serve(runner):
    result = runner.invoke(serve)
    assert result.exit_code == 0


def test_serve_help(runner):
    result = runner.invoke(serve, ["--help"])
    assert "Run the OpenFisca Web API" in result.output


def test_test(runner):
    result = runner.invoke(test)
    assert result.exit_code == 0


def test_test_help(runner):
    result = runner.invoke(test, ["--help"])
    assert "Run OpenFisca YAML tests" in result.output
