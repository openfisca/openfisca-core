from pytest import fixture

from openfisca_cli.commands import openfisca, serve, test


def test_openfisca(cli_runner):
    result = cli_runner.invoke(openfisca).output
    assert "Usage: openfisca [OPTIONS] COMMAND [ARGS]" in result
    assert "-h, --help  Show this message and exit." in result
    assert "serve  Run the OpenFisca Web API" in result
    assert "test   Run OpenFisca YAML tests" in result


def test_openfisca_serve(cli_runner):
    result = cli_runner.invoke(serve)
    assert result.exit_code == 0


def test_openfisca_test(cli_runner):
    result = cli_runner.invoke(test)
    assert result.exit_code == 0
