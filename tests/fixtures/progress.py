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

    class _ProgressBar(SupportsProgress):

        def __init__(self):
            self.called = []

        def init(self):
            ...

        def push(self, count, __total):
            self.called.append(Call(name(), count))

        def okay(self, message):
            self.called.append(Call(name(), message))

        def info(self, message):
            self.called.append(Call(name(), message))

        def warn(self, message):
            self.called.append(Call(name(), message))

        def fail(self):
            self.called.append(Call(name()))

        def then(self):
            ...

        def wipe(self):
            ...

    return _ProgressBar()
