import os
import sys

import pytest

from openfisca_tasks import CheckVersion


@pytest.fixture
def checker(bar):
    """A version checker."""

    checker = CheckVersion(bar)
    checker.parser = type(checker.parser)(this = "34.0.0", that = "34.0.0")
    checker.bumper.this = "34.0.0"
    checker.bumper.that = "34.0.0"
    return checker


def test_check_version(checker):
    """Prints status updates to the user."""

    checker()
    infos = (call.args for call in checker.bar.called if call.name == "info")

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit.index)

    assert next(infos) == "Parsing files from 34.0.0…\n"
    assert next(infos) == "Parsing files from 34.0.0…\n"
    assert next(infos) == "Checking for functional changes…\n"
    assert next(infos) == "Checking for added functions…\n"
    assert next(infos) == "Checking for removed functions…\n"
    assert next(infos) == "Version bump required: NONE!\n"
    assert exit.value.code == os.EX_OK


def test_files_when_no_diff(checker):
    """Passes when there are no file diffs."""

    checker()
    calls = [call.args for call in checker.bar.called]

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit.index)

    assert not any(call for call in checker.bar.called if call.name == "warn")
    assert "Version bump required: NONE!\n" in calls
    assert exit.value.code == os.EX_OK


def test_files_when_diff_is_not_functional(checker):
    """Does not require a version bump files are not functional."""

    checker.parser.diff = ["README.md"]
    checker()
    calls = [call.args for call in checker.bar.called]

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit.index)

    assert "Version bump required: NONE!\n" in calls
    assert exit.value.code == os.EX_OK


def test_files_when_diff_is_functional(checker):
    """Requires a patch bump when there are file diffs."""

    checker.parser.diff = ["file.py"]
    checker()
    calls = [call.args for call in checker.bar.called]

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit.index)

    assert "~ file.py\n" in calls
    assert "Version bump required: PATCH!\n" in calls
    assert exit.value.code != os.EX_OK


def test_files_when_diff_only_parse_changed(checker):
    """Only go inspect changed files."""

    checker.parser = type(checker.parser)(this = "35.1.0", that = "35.0.0")
    checker()
    calls = [call.args for call in checker.bar.called]
    assert "+ tools.__init__.assert_datetime_equals\n" in calls

    checker.parser.diff = []
    checker.bar.called = []
    checker()
    calls = [call.args for call in checker.bar.called]
    assert "+ tools.__init__.assert_datetime_equals\n" not in calls

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit.index)

    assert "Version bump required: MINOR!\n" in calls
    assert exit.value.code != os.EX_OK


def test_funcs_when_no_diff(checker):
    """Does not warn if there are no diffs."""

    checker()
    bar = checker.bar
    calls = [call.args for call in bar.called if isinstance(call.args, str)]

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit.index)

    assert len("".join(calls).split("~")) == 1
    assert len("".join(calls).split("+")) == 1
    assert len("".join(calls).split("-")) == 1
    assert "Version bump required: NONE!\n" in calls
    assert exit.value.code == os.EX_OK


def test_funcs_when_added(checker):
    """Requires a minor bump when a function is added."""

    checker.parser = type(checker.parser)(this = "35.1.0", that = "35.0.0")
    checker()
    bar = checker.bar
    calls = [call.args for call in bar.called if isinstance(call.args, str)]

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit.index)

    assert len("".join(calls).split("+")) > 1
    assert len("".join(calls).split("-")) == 1
    assert "Version bump required: MINOR!\n" in calls
    assert exit.value.code != os.EX_OK


def test_funcs_when_removed(checker):
    """Requires a major bump when a function is removed."""

    checker.parser = type(checker.parser)(this = "35.0.0", that = "34.7.0")
    checker()
    bar = checker.bar
    calls = [call.args for call in bar.called if isinstance(call.args, str)]

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit.index)

    assert len("".join(calls).split("-")) > 1
    assert "Version bump required: MAJOR!\n" in calls
    assert exit.value.code != os.EX_OK


def test_funcs_when_duplicates(checker):
    """Gives a unique name to all contracts in the same module."""

    checker.parser = type(checker.parser)(this = "HEAD", that = "35.5.1")
    checker()
    bar = checker.bar
    calls = [call.args for call in bar.called if isinstance(call.args, str)]

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit.index)

    assert "+ openfisca_tasks._builder.total#getter\n" in calls
    assert "+ openfisca_tasks.bar.init(bis)\n" in calls
    assert "+ openfisca_tasks.bar.init\n" in calls
    assert "Version bump required: MAJOR!\n" in calls
    assert exit.value.code != os.EX_OK
