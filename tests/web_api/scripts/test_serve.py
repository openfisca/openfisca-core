from argparse import ArgumentParser

from pytest import fixture

from openfisca_web_api.scripts.serve import (
    create_server_parser,
    parse_args,
    read_user_config,
    update,
    )


@fixture
def parser():
    return ArgumentParser()


@fixture
def make_args(parser, mocker):
    def _make_args(args = {}):
        argv = mocker.patch("sys.argv", [])

        for key, value in args.items():
            parser.add_argument(key)
            argv += [key, value]

        return vars(parser.parse_args(argv))

    return _make_args


def test_create_server_parser():
    result = create_server_parser()
    assert isinstance(result, ArgumentParser)


def test_parse_args(parser):
    assert parse_args(parser, []) == {}


def test_read_user_config(make_args):
    assert not read_user_config({}, make_args(), {})


def test_read_user_config_with_configiguration_file(mocker, make_args):
    serve_open = mocker.patch("openfisca_web_api.scripts.serve.open")
    serve_exec = mocker.patch("openfisca_web_api.scripts.serve.exec")
    user_args = make_args({"--configuration-file": "server.cfg"})
    read_user_config({}, user_args, {})
    assert serve_open.call_count == 1
    assert serve_exec.call_count == 1


def test_update():
    result = update({"bind": "localhost:1234"}, {"port": 2345})
    assert result == {"bind": "localhost:2345", "port": 2345}
