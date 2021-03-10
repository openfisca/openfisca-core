from argparse import ArgumentParser

from pytest import fixture

from openfisca_web_api.scripts.serve import (
    create_server_parser,
    parse_args,
    read_user_configuration,
    )


@fixture
def parser():
    return ArgumentParser()


def test_create_server_parser():
    result = create_server_parser()
    assert isinstance(result, ArgumentParser)


def test_parse_args(parser):
    assert parse_args(parser, []) == {}


def test_read_user_configuration():
    result = read_user_configuration({}, {}, {})
    assert not result
