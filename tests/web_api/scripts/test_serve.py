from argparse import ArgumentParser

from pytest import fixture

from openfisca_web_api.scripts.serve import (
    create_gunicorn_parser,
    parse_args,
    read_user_configuration,
    )


@fixture
def parser():
    return ArgumentParser()


def test_create_gunicorn_parser():
    result = create_gunicorn_parser()
    assert isinstance(result, ArgumentParser)


def test_parse_args(parser):
    assert parse_args(parser, []) == {}
