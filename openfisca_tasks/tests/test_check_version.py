from openfisca_tasks import CheckVersion


def test_check_version_when_no_changes(progress):
    """It passes when there are no changes."""

    checker = CheckVersion()
    checker(progress)
