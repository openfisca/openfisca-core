from pytest import fixture

from openfisca_cli.commands import openfisca, serve, test


def test_openfisca(cli_runner):
    result = cli_runner.invoke(openfisca)
    output = result.output
    assert "Usage: openfisca [OPTIONS] COMMAND [ARGS]" in output
    assert "-h, --help  Show this message and exit." in output
    assert "serve  Run the OpenFisca Web API" in output
    assert "test   Run OpenFisca YAML tests" in output


def test_openfisca_serve(mocker, cli_runner):
    run_serve = mocker.patch("openfisca_cli.commands.run_serve")
    cli_runner.invoke(serve)
    assert run_serve.call_count == 1


def test_openfisca_test(mocker, cli_runner):
    run_test = mocker.patch("openfisca_cli.commands.run_test")
    cli_runner.invoke(test)
    assert run_test.call_count == 1
