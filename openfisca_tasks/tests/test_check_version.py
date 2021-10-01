import inspect
from typing import NamedTuple

import pytest

from openfisca_tasks import CheckVersion

from .._protocols import SupportsProgress


@pytest.fixture
def progress():

    def name():
        return inspect.stack()[1][3]

    class Call(NamedTuple):
        name: str
        args: str = None

    class ProgressBar(SupportsProgress):

        def init(self):
            self.called = []

        def push(self, __count, __total):
            ...

        def info(self, __message):
            ...

        def warn(self, message):
            self.called.append(Call(name(), message))

        def fail(self):
            self.called.append(Call(name()))

        def wipe(self):
            ...

    return ProgressBar()


def test_check_version_when_no_changes(progress):
    """It passes when there are no changes."""

    checker = CheckVersion()
    checker(progress)
