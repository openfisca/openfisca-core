import re

import pytest

from openfisca_tasks import Bar

COLORS = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


@pytest.fixture
def bar():
    """A progress bar."""

    return Bar()


@pytest.fixture
def capture(capsys):
    """Capture prints."""

    def _capture():
        # We strip colors to test just content.
        return COLORS.sub("", capsys.readouterr().out)

    return _capture


def test_init(bar, capture):
    bar.init()
    output = "[/] 0%   |··················································|\r"
    assert capture() == output


def test_push(bar, capture):
    bar.push(0, 2)
    output = "[/] 50%  |✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓·························|\r"
    assert capture() == output


def test_okay(bar, capture):
    bar.okay("Hello!")
    output = "[✓] Hello!"
    assert capture() == output


def test_info(bar, capture):
    bar.info("Hello!")
    output = "[i] Hello!"
    assert capture() == output


def test_warn(bar, capture):
    bar.warn("Hello!")
    output = "[!] Hello!"
    assert capture() == output


def test_fail(bar, capture):
    bar.fail()
    output = "\r[x]"
    assert capture() == output


def test_then(bar, capture):
    bar.then()
    output = "\n\r"
    assert capture() == output


def test_wipe(bar, capture):
    bar.wipe()
    output = "                                                             \r"
    assert capture()[-62:] == output
