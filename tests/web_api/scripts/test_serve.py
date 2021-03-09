from argparse import ArgumentParser

from pytest import fixture

from openfisca_web_api.scripts.serve import (
    create_gunicorn_parser,
    read_user_configuration,
    )


@fixture
def parser():
    parser = ArgumentParser()
    parser.add_argument('--configuration-file')
    return parser


def test_create_gunicorn_parser():
    result = create_gunicorn_parser()
    assert isinstance(result, ArgumentParser)
