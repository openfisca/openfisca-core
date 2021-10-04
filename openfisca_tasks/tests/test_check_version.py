import os
import sys

import pytest

from openfisca_tasks import CheckVersion


@pytest.fixture
def checker(progress):
    """A version checker."""

    checker = CheckVersion(progress)
    checker.parser.actual_files = ()
    checker.parser.before_files = ()
    checker.parser.changed_files = ()
    checker.bumper.before = "0.5.0"
    checker.bumper.actual = "0.5.0"
    return checker


def test_check_version(checker):
    """Prints status updates to the user."""

    checker()
    bar = checker.progress
    infos = (call.args for call in bar.called if call.name == "info")

    assert next(infos) == "Parsing files from HEAD…\n"
    assert next(infos) == "Parsing files from 0.5.0…\n"
    assert next(infos) == "Checking for functional changes…\n"
    assert next(infos) == "Checking for added functions…\n"
    assert next(infos) == "Checking for removed functions…\n"
    assert next(infos) == "Version bump required: NONE!\n"

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit.index)

    assert exit.value.code == os.EX_OK


def test_when_files_no_diff(checker):
    """Passes when there are no file diffs."""

    checker()
    bar = checker.progress
    calls = [call.args for call in bar.called]

    assert not any(call for call in bar.called if call.name == "warn")
    assert "Version bump required: NONE!\n" in calls

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit.index)

    assert exit.value.code == os.EX_OK


def test_when_files_when_diff_no_functional(checker):
    """Does not require a version bump files are not functional."""

    checker.parser.changed_files = ["README.md"]
    checker()
    bar = checker.progress
    calls = [call.args for call in bar.called]

    assert f"Version bump required: NONE!\n" in calls

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit.index)

    assert exit.value.code == os.EX_OK


def test_when_files_when_diff_functional(checker):
    """Requires a patch bump when there are file diffs."""

    checker.parser.changed_files = ["file.py"]
    checker()
    bar = checker.progress
    calls = [call.args for call in bar.called]

    assert "~ file.py\n" in calls
    assert f"Version bump required: PATCH!\n" in calls

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit.index)

    assert exit.value.code != os.EX_OK


def test_when_files_when_diff_only_parse_changed(checker):
    """Only builds contracts of the changed files."""

    checker.parser.actual_files = ["openfisca_tasks/check_version.py"]
    checker.parser.before_files = ["openfisca_core/calmar.py"]
    checker.parser.changed_files = checker.parser.actual_files
    checker()
    bar = checker.progress
    calls = [call.args for call in bar.called]
    # files = [contract.file for contract in checker.parser.contracts]

    assert "~ openfisca_tasks/check_version.py\n" in calls
    assert "~ openfisca_core/calmar.py\n" not in calls
    assert "+ openfisca_tasks.check_version.__init__\n" in calls

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit.index)

    assert exit.value.code != os.EX_OK
