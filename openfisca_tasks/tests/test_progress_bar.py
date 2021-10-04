import re

import pytest

from openfisca_tasks import ProgressBar

COLORS = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


@pytest.fixture
def progress():
    """A progress bar."""

    return ProgressBar()


@pytest.fixture
def capture(capsys):
    """Capture prints."""

    def _capture():
        # We strip colors to test just content.
        return COLORS.sub("", capsys.readouterr().out)

    return _capture


def test_init(progress, capture):
    progress.init()
    output = "[/] 0%   |··················································|\r"
    assert capture() == output


def test_push(progress, capture):
    progress.push(0, 2)
    output = "[/] 50%  |✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓·························|\r"
    assert capture() == output


def test_okay(progress, capture):
    progress.okay("Hello!")
    output = "[✓] Hello!"
    assert capture() == output


def test_info(progress, capture):
    progress.info("Hello!")
    output = "[i] Hello!"
    assert capture() == output


def test_warn(progress, capture):
    progress.warn("Hello!")
    output = "[!] Hello!"
    assert capture() == output


def test_fail(progress, capture):
    progress.fail()
    output = "\r[x]"
    assert capture() == output


def test_then(progress, capture):
    progress.then()
    output = "\n\r"
    assert capture() == output


def test_wipe(progress, capture):
    progress.wipe()
    output = "                                                             \r"
    assert capture()[-62:] == output
