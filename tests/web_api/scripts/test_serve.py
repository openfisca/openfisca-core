from argparse import ArgumentParser
from errno import EINVAL

from pytest import fixture, raises

from openfisca_web_api.scripts.serve import (
    OpenFiscaWebAPIApplication,
    main,
    read_config,
    update_config,
    )


@fixture
def parser():
    return ArgumentParser()


@fixture
def vector(mocker):
    return mocker.patch("openfisca_web_api.scripts.serve.sys.argv", [])


@fixture
def make_args(mocker, parser, vector):
    def _make_args(args = None):
        # To avoid passing pytest arguments to argparse
        nonlocal vector

        if args is not None:
            for key, value in args.items():
                parser.add_argument(key)
                vector += [key, value]

        return vars(parser.parse_args(vector))

    return _make_args


def test_read_config(make_args):
    assert not read_config({}, make_args(), {})


def test_read_config_with_configiguration_file(mocker, make_args):
    serve_open = mocker.patch("openfisca_web_api.scripts.serve.open")
    serve_exec = mocker.patch("openfisca_web_api.scripts.serve.exec")
    user_args = make_args({"--configuration-file": "server.cfg"})
    read_config({}, user_args, {})
    serve_open.assert_called_once_with("server.cfg", "r")
    serve_exec.assert_called_once()


def test_update_config():
    result = update_config({"bind": "localhost:1234"}, {"port": 2345})
    assert result == {"bind": "localhost:2345", "port": 2345}


def test_web_api():
    assert OpenFiscaWebAPIApplication({})


def test_main(mocker, parser, vector):
    web_api = mocker.patch("openfisca_web_api.scripts.serve.OpenFiscaWebAPIApplication")
    vector += [""]
    main(parser)
    web_api.assert_called_once()


def test_main_with_invalid_arguments(mocker, parser, vector):
    vector += ["", "format C:"]

    with raises(SystemExit) as exit:
        main(parser)

    assert exit.value.code == EINVAL
