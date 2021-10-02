import os
import sys

import pytest

from openfisca_tasks import CheckVersion


def test_check_version_when_no_changes(progress):
    """It passes when there are no changes."""

    checker = CheckVersion([])
    checker(progress)

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit)

    assert exit.value.code == os.EX_OK


def test_check_version_when_changes(progress):
    """It fails when there are changes."""

    checker = CheckVersion(["foo"])
    checker(progress)

    with pytest.raises(SystemExit) as exit:
        sys.exit(checker.exit)

    assert exit.value.code != os.EX_OK
