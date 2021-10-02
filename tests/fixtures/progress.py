import inspect
from typing import NamedTuple

import pytest

from openfisca_tasks import SupportsProgress


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

        def push(self, count, total):
            ...

        def okay(self, message):
            ...

        def info(self, message):
            ...

        def warn(self, message):
            self.called.append(Call(name(), message))

        def fail(self):
            self.called.append(Call(name()))

        def next(self):
            ...

        def wipe(self):
            ...

    return ProgressBar()
